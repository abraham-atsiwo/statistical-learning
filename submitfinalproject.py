# -*- coding: utf-8 -*-
"""SubmitFinalProject.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/12z_6Conlr-3HsNNmocp6QjKn2V8Pg7dp
"""

#import modules
from __future__ import division
import torch
import numpy as np
from matplotlib import pyplot as plt
from mpl_toolkits import mplot3d
plt.style.use('seaborn-poster')
from scipy.special import gamma
import pandas as pd

device =  'cuda:0' if torch.cuda.is_available else 'cpu'
dtype = torch.float64
device = 'cpu'
device

def generate_data(size=100000, low=-0.5, high=0.5, type_n=3, prop=0.5, custom_data=None, n_each=None):
    if custom_data is not None:
      size = len(custom_data)   
    #output vector
    c1, c2 = [], []
    #define the radius and length
    ll = high - low
    center = np.repeat((low+high)/2, type_n)
    n_volume = ll**type_n
    
    #checking whether the proportion is valid
    r_max = high - center[0]
    prop_max = (1/n_volume)*(r_max**type_n*(np.pi**(0.5*type_n)))*(1/gamma(type_n*0.5+1))
    
    #radius
    prop_volume = prop*n_volume
    radius_sq = ((prop_volume*gamma((type_n/2)+1))/(np.pi**(type_n*0.5)))**(2/type_n)
       
    for j in range(size):
        #generate from uniform distribution
        if custom_data is None:
          tmp = np.random.uniform(low=low, high=high, size=type_n)
        else:
          tmp = custom_data[j]
        tmp_sum = np.sum((tmp-center)**2)

        if tmp_sum <= radius_sq:
            c2.append(tmp)
        else:
            c1.append(tmp)  

    #type conversion
    cube, sphere = np.array(c1), np.array(c2)

    if n_each is not None:
      cube = cube[:n_each]
      sphere = sphere[:n_each]
    
    features = np.concatenate((cube, sphere), axis=0)
    target = np.concatenate((np.zeros(len(cube)), np.ones(len(sphere))))
    target = pd.get_dummies(target).values

    return cube, sphere, features, target, np.round(prop_max, 4), len(sphere)/size

"""### Loading Data"""

y_train = pd.read_csv('y_train.csv')
x_train = pd.read_csv('x_train.csv')
x_train, y_train = np.array(x_train), np.array(y_train)
x_train, y_train

"""### `Utility Functions`"""

def sigmoid(x):
  x = torch.tensor(x, device=device, dtype=dtype)
  return 1 / (1 + torch.exp(-x))

def mse(target, predicted):
  res = target[:,0] != predicted[:,0]
  return np.mean(res)

"""### Comparing Algorithms

- Back Propagation
"""

class backPropagation():

  def __init__(self, dimension=None, activation_fun = None, device=device, niter=100000, dtype=torch.float64):
    self.dimension = dimension
    self.activation_fun = activation_fun
    self.device = device
    self.niter = niter
    self.dtype=dtype

    #initialize weights
    input_size = self.dimension[0]
    hidden_size = self.dimension[1]
    output_size = self.dimension[2]
    
    #initializing weight for the hidden layer
    self.W1 = torch.randn((input_size, hidden_size), device=self.device, dtype=dtype)
    # initializing weight for the output layer
    self.W2 = torch.randn((hidden_size , output_size), device=self.device, dtype=dtype)
 
    #bias parameter
    bias_W1 = torch.randn((1, hidden_size), device=self.device, dtype=dtype)
    bias_W2 = torch.randn((1, output_size), device=self.device, dtype=dtype)

    #weight with bias
    self.W1_constant = torch.concat((self.W1, bias_W1), axis=0)
    self.W2_constant = torch.concat((self.W2, bias_W2), axis=0)

  def fit(self, xtrain=None, ytrain=None, learning_rate=0.1):
    N, p = xtrain.shape
    xtrain = torch.tensor(xtrain, device=self.device)
    #xtrain = torch.from_numpy(xtrain).type(self.dtype).to(self.device)
    ytrain = torch.tensor(y_train, device=device)
    bias = torch.ones((N,1), device=self.device)
    features = torch.concat((xtrain, bias), axis=1)
    features = torch.tensor(features)

    for itr in range(self.niter):
      Z1 = features @ self.W1_constant
      A1 = self.activation_fun(Z1)
      A1_bias = torch.concat((A1, bias), axis=1)
      #output layer
      Z2 = A1_bias @ self.W2_constant
      A2 = self.activation_fun(Z2)
      E1 = A2 - ytrain
      # backpropagation
      E1 = A2 - ytrain
      #err_norm.append(E1)
      dW1 = E1 * A2 * (1 - A2)
      E2 = dW1 @ self.W2.T
      dW2 = E2 * A1 * (1 - A1)
      #update weight
      W2_update = A1_bias.T @ dW1
      W1_update = features.T @ dW2
      self.W2_constant = self.W2_constant - (learning_rate * W2_update)
      self.W1_constant = self.W1_constant - (learning_rate * W1_update)
      self.W2 = self.W2_constant[:-1, :]

  def predict(self, xtest):
    xtest = torch.tensor(xtest, device=self.device, dtype=self.dtype)
    const = torch.ones((len(xtest),1), dtype=dtype, device=device)
    features_bias= torch.concat((xtest, const), axis=1)
    Z = sigmoid(features_bias @ self.W1_constant)
    Z = torch.concat((Z, const), axis=1)
    out = sigmoid(Z @ self.W2_constant)
    output = out.cpu().numpy()
    predicted = pd.get_dummies(np.argmax(output, axis=1)).values
    #return
    return predicted

     
model = backPropagation([3,6,2], device=device, activation_fun=sigmoid)
model.fit(x_train, y_train)
ypred = model.predict(x_train)
ypred

mse(ypred, y_train)

"""### `Test Data`"""

h = 0.02
#h = 0.1
dataStep = np.arange(-0.5, 0.5001, h)
dataGrid = np.array([[i,j,k] for i in dataStep for j in dataStep for k in dataStep])
df = generate_data(custom_data=dataGrid)
xtest = df[2]
ytest = df[3]
xtest, ytest

xtest.shape, ytest.shape
np.savetxt('x_test.csv', xtest, delimiter=',')
np.savetxt('y_test.csv', ytest, delimiter=',')

ypred_test = model.predict(xtest)
mse(ytest, ypred_test)

"""### Confusion matrix"""

from sklearn.metrics import confusion_matrix
confusion_matrix(ytest[:,0], ypred_test[:,0])

"""### `K-Nearest Neighbors`"""

def euclideanDistance(x,y):
  tmp = x-y
  return np.sqrt(np.dot(tmp, tmp))

def absDistance(x, y):
  return np.sum(x-y)

class kNN():

  def __init__(self, k, distFunc=None):
    self.k = k
    self.distanceFunction = distFunc

  def _fitPredict(self, xrow):
    xtrain = self.xtrain
    ytrain = self.ytrain
    dist = np.apply_along_axis(euclideanDistance, 1, xtrain, xrow)
    dist_ind = sorted(range(len(dist)), key = lambda sub: dist[sub])[:self.k]
    number_list = ytrain[dist_ind]
    (unique, counts) = np.unique(number_list, return_counts=True)
    prop = counts/self.k
    kSmall = min(prop)
    ind = list(prop).index(kSmall)
    return unique[ind]

  def fitPredict(self, xtrain=None, ytrain=None, xtest=None):
    self.xtrain = xtrain
    self.ytrain = ytrain

    if xtest is None:
      xtest = xtrain
    else:
      xtest = xtest
    ypred = np.apply_along_axis(self._fitPredict, 1, xtest)
    return ypred

  def mse(self, yhat, y):
    return np.mean(yhat != y)

  def accuracy(self, yhat, y):
    return 1 - self.mse(yhat, y)

"""#### Prediction"""

''' model = kNN(1, absDistance)
y_train_mod = y_train[:,0]
y_test = ytest[:,0]
yhat = model.fitPredict(x_train, y_train_mod, x_train)
model.mse(yhat, y_train_mod) '''

model = kNN(2, euclideanDistance)
y_train_mod = y_train[:,0]
y_test = ytest[:,0]
yhat = model.fitPredict(x_train, y_train_mod, x_train)
model.mse(yhat, y_train_mod)

"""#### Test Data"""

model = kNN(2, euclideanDistance)
yhat = model.fitPredict(x_train, y_train_mod, xtest)
model.mse(yhat, y_test)

confusion_matrix(yhat, y_test)

"""#### Prediction for `N=4`"""

y_train1 = pd.read_csv('y_train4.csv')
x_train1 = pd.read_csv('x_train4.csv')
x_train1, y_train1 = np.array(x_train1), np.array(y_train1)
x_train1, y_train1



"""#### Test Data"""

h = 0.055
#h = 0.1
dataStep = np.arange(-0.5, 0.5001, h)
dataGrid1 = np.array([[i,j,k, w] for i in dataStep for j in dataStep for k in dataStep for w in dataStep])
df1 = generate_data(custom_data=dataGrid1, type_n=4)
xtest1 = df1[2]
ytest1 = df1[3]
xtest1, ytest1.shape

np.savetxt('x_test1.csv', xtest1, delimiter=',')
np.savetxt('y_test1.csv', ytest1, delimiter=',')

"""#### Back Propagation"""

model1 = backPropagation([4,5,2], device=device, activation_fun=sigmoid, niter=400000)
model1.fit(x_train1, y_train1)
ypred1 = model1.predict(xtest1)
ypred1

mse(ypred1, ytest1)

confusion_matrix(ypred1[:,0], ytest1[:,0])

"""### KNN"""

model = kNN(2, euclideanDistance)
y_train_mod1 = y_train1[:,0]
y_test1 = ytest1[:,0]
yhat = model.fitPredict(x_train1, y_train_mod1, x_train1)
model.mse(yhat, y_train_mod1)

model = kNN(2, euclideanDistance)
y_train_mod1 = y_train1[:,0]
y_test1 = ytest1[:,0]
yhat = model.fitPredict(x_train1, y_train_mod1, xtest1)
model.mse(yhat, y_test1)

confusion_matrix(yhat, y_test1)