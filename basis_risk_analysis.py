# -*- coding: utf-8 -*-
"""
Created on Fri Oct 18 14:00:54 2019

@author: jkern
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy.stats as st
from sklearn import linear_model

# LOAD RELEVANT DATA

# read in excel file with price data
df_prices = pd.read_excel('SPP_LMPs.xlsx',sheet_name='Historical LMP',header=1)

# selecting only real time nodal prices for 2015
rtn2015 = df_prices['RT_NODE_2015']

# exclude the NAN values
rtn2015_edit = rtn2015.iloc[:8760]

# selecting only real time nodal prices for 2016
rtn2016 = df_prices['RT_NODE_2016']

# append 2015 and 2016 prices
rtn_both = rtn2015_edit.append(rtn2016)

# convert to numerical array
RTN = np.array(rtn_both)

#plot 2015 and 2016 nodal prices
plt.plot(RTN)
plt.xlabel('Hour')
plt.ylabel('Price $/MWh')
plt.show()

#now do the same thing with hub prices

# selecting only real time hub prices for 2015
rth2015 = df_prices['RT_HUB_2015']

# exclude the NAN values
rth2015_edit = rth2015.iloc[:8760]

# selecting only real time hub prices for 2016
rth2016 = df_prices['RT_HUB_2016']

# append 2015 and 2016 prices
rth_both = rth2015_edit.append(rth2016)

# convert to numerical array
RTH = np.array(rth_both)

#plot 2015 and 2016 hub prices
plt.plot(RTH,color='r')
plt.xlabel('Hour')
plt.ylabel('Price $/MWh')
plt.show()

df_RTH = pd.DataFrame(RTH)
df_RTH.columns = ['Value']
df_RTH.to_csv('clean_HUB_PRICES.csv')

df_RTN = pd.DataFrame(RTN)
df_RTN.columns = ['Value']
df_RTN.to_csv('clean_NODE_PRICES.csv')

########################################################################

#now read in wind power data

# read in excel file with wind speed data
df_wind = pd.read_excel('SPP_wind data_20180309.xlsx',sheet_name='Historical 8760s',header=14)

# selecting only wind power for 2015
wind2015 = df_wind['2015_MWh']

# exclude the NAN values
wind2015_edit = wind2015.iloc[:8760]

# selecting only wind power for 2016
wind2016 = df_wind['2016_MWh']

# append 2015 and 2016 wind power
wind_both = wind2015_edit.append(wind2016)

# convert to numerical array
WIND = np.array(wind_both)

#plot 2015 and 2016 hub prices
plt.plot(WIND,color='g')
plt.xlabel('Hour')
plt.ylabel('Energy (MWh')
plt.show()

#########################################################################

# difference between hub price and node price
basis_difference = RTH - RTN

#scatter plot of wind (x axis) and basis risk (y axis)
plt.scatter(WIND,basis_difference,c='orange',alpha=0.5,edgecolors='black')
plt.xlabel('Wind (MWh)')
plt.ylabel('Hub minus Node ($/MWh)')

# combine wind and basis risk data into a single array
combined = np.column_stack((WIND,basis_difference))

# convert single array to pandas dataframe and rename columns
df_combined = pd.DataFrame(combined)
df_combined.columns = ['Wind','Basis_Risk']

# drop NaN values from dataframe
cleaned = df_combined.dropna()

# calculate pearson R correlation
r = st.pearsonr(cleaned['Wind'],cleaned['Basis_Risk'])
print('The correlation and p-value are ' + str(r))


#########################################################################

#read in electricity demand data

# set counter equal to 0
counter = 0

# iterate over two years
for year in range(2015,2017):
    
    # iterate over 12 months    
    for i in range(1,13):
            
        #base of filename
        base = 'HOURLY_LOAD-' + str(year)
        
        if i < 10:
            adder = '0' + str(i)
        else:
            adder = str(i)
        
        #specify filename to read
        filename = base + adder + '.csv'
        
        #read data 
        data = pd.read_csv(filename,header=0)
  
        # if it's the first month we're reading in, set demand = data
        if counter < 1:
             
            demand = data
        
        # otherwise, stack new data underneath old data
        else:
            
            demand = pd.concat((demand,data),sort=False)
        
        counter = counter + 1
    
#get rid of duplicate values
shortened = demand.drop_duplicates()

#reset index
S = shortened.reset_index(drop=True)

#calculate total SPP demand
SPP_total =[]
for i in range(0,len(S)):
    total = np.sum(S.loc[i,' CSWS':' WR'])
    if total >0:
        SPP_total.append(total)
        
#plot SPP electricity demand
plt.figure()
plt.plot(SPP_total,color='b')
plt.xlabel('Hour')
plt.ylabel('Demand (MWh')
plt.show()

df_SPP = pd.DataFrame(SPP_total)
df_SPP.columns = ['Value']
df_SPP.to_csv('clean_DEMAND.csv')


#scatter plot of wind (x axis) and basis risk (y axis)
plt.scatter(SPP_total,basis_difference,c='blue',alpha=0.3,edgecolors='black')
plt.xlabel('Demand(MWh)')
plt.ylabel('Hub minus Node ($/MWh)')

# combine wind and basis risk data into a single array
combined = np.column_stack((SPP_total,basis_difference))

# convert single array to pandas dataframe and rename columns
df_combined = pd.DataFrame(combined)
df_combined.columns = ['Demand','Basis_Risk']

# drop any NaN values from dataframe
cleaned2 = df_combined.dropna()

# calculate pearson R correlation
r = st.pearsonr(cleaned2['Demand'],cleaned2['Basis_Risk'])
print('The correlation and p-value are ' + str(r))

#############################################
# multivariate regresssion of wind production, demand, and basis risk

# combine wind and basis risk data into a single array
combined = np.column_stack((WIND,SPP_total,basis_difference))
df_combined = pd.DataFrame(combined)
df_combined.columns = ['Wind','Demand','Basis_Risk']
cleaned = df_combined.dropna()

# define linear regression object
reg = linear_model.LinearRegression()

# Train the models using a training set
X = np.column_stack((cleaned['Wind'],cleaned['Demand']))
reg.fit(X,cleaned['Basis_Risk'])

# print intercept
print(reg.intercept_)

# print coefficients
print(reg.coef_)

# regression equation
# y = coef#1 * wind + coef#2 * demand + intercept

W = cleaned.loc[:,'Wind']
D = cleaned.loc[:,'Demand']
B = cleaned.loc[:,'Basis_Risk']

# estimating basis risk as a function of wind and demand
Y = []
for i in range(0,len(W)):
    
    y_hat = reg.coef_[0]*W.iloc[i] + reg.coef_[1]*D.iloc[i] + reg.intercept_
    
    Y.append(y_hat)
    
# compare estimated and actual basis risk
plt.figure()
plt.plot(B[0:500],'b')
plt.plot(Y[0:500],'r')
plt.ylabel('Basis Risk ($/MWh)')
plt.xlabel('Hour')

# error analysis 
errors = Y - B
plt.figure()
plt.hist(errors,200)
plt.xlabel('Error ($/MWh)')
plt.ylabel('Frequency')

# model basis risk as function of fitted regression + synthetic errors sampled
# from fitted distribution

# best fit distribution: st.cauchy
best_fit_params = [8.929849945,8.0275377602]

# generate # of random samples from best fit distribution

empty = []
for i in range(0,len(errors)):
    
    count = 0
    
#    print(i)
    e = st.cauchy.rvs(loc=best_fit_params[0], scale=best_fit_params[1], size=1)
    
    while e > 45 or e < -700:
        e = st.cauchy.rvs(loc=best_fit_params[0], scale=best_fit_params[1], size=1)
        count = count + 1
        
        if count > 100:
            e = 0
            break
        
    empty.append(float(e))
    
plt.hist(empty,50,alpha=0.5)


        
        
    