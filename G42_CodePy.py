# -*- coding: utf-8 -*-
"""SentimentalAnalysisRecommendationSys.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1NLTTTkGXKRbnZRTvtEehd_xyAXn2GkiI

Machine Learning for Sentiment Analysis and Recommendation System

Team G42</br>
Janghyuk Boo, 40005573</br>
Mona Shayvard, 40061450
"""

import pandas as pd
import tensorflow as tf
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import re
import nltk
from nltk.tokenize import  word_tokenize
from nltk.stem import PorterStemmer
from nltk.stem import WordNetLemmatizer 
from nltk.corpus import stopwords
from google.colab import drive
!pip install langdetect
import langdetect
from langdetect import detect
import matplotlib.pyplot as plt 
from matplotlib import rcParams
import seaborn as sns
from textblob import TextBlob
from plotly import tools
import plotly.graph_objs as go
from plotly.offline import iplot
from sklearn.model_selection import train_test_split
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.naive_bayes import GaussianNB
import matplotlib.pyplot as plt

#drive.mount('/content/drive')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('stopwords')
nltk.download('wordnet')

df = pd.read_csv("7282_1.csv")

"""**Hotel Review data**"""

df.head(5)
df[['address','categories','latitude','name','postalCode','reviews.date','reviews.rating','reviews.text' ]]

"""# ***Data Preprocessing***
**Removing Non English review**
"""

df.dropna(subset=['reviews.text'],inplace=True)
df['reviews.text'].isnull().sum()

def addLang(text):
  try:
    language = detect(text)
  except:
    language = "error"
    print("This row throws and error:", text)
  return language

df['lang'] = df['reviews.text'].apply(lambda row: addLang(row))
dfNew = df[df['lang']!= 'error']
print(len(dfNew[dfNew['lang']== 'en']))

dfNew = dfNew[dfNew['lang']== 'en']
dfNew['reviews.text'].head(2)

"""**Removing Stopwords and Tokenizer**"""

stopWords = nltk.corpus.stopwords.words('english')
lemmatizer = WordNetLemmatizer() 
def preprocess(text): #we can add to this 
  #text = re.sub('.|,', ' ', text)
  tokenized = nltk.word_tokenize(text.lower())
  removedStopWords = [w for w in tokenized if w not in stopWords]
  puncRemoved = [w for w in removedStopWords if w.isalpha()]
  lemmatized = [lemmatizer.lemmatize(w) for w in puncRemoved]
  return lemmatized
  
dfNew['preprocessed'] = dfNew['reviews.text'].apply(lambda text: preprocess(text))

dfNew.columns

"""**Processing date format & review rate**"""

dfNew = dfNew[dfNew['reviews.rating']	 < 6]
dfNew['reviews.rating'] = dfNew['reviews.rating'].astype(int)
positive = dfNew[dfNew['reviews.rating']>=4]
negative = dfNew[dfNew['reviews.rating']<2]
new = dfNew["reviews.date"].str.split("-", n = 1, expand = True) 
  
# making separate date column from new data frame 
dfNew["year"]= new[0] 
dfNew["Month"]= (new[1].str)[0:2]
dfNew["time"]= (new[1].str)[6:11]
dfNew=dfNew.drop(['reviews.date'], axis=1)
dfNew.head(2)

"""**Review Rate**"""

sns.countplot(dfNew['reviews.rating'], label ='Count')

dfNew[['preprocessed']].head(2)

"""**Data Scaling**"""

#Reduced the size of data 
newdf=dfNew[['name','reviews.rating','reviews.text','preprocessed']]
newdf['feedback'] = None
newdf.drop(newdf.index[10000:], inplace=True)
newdf.head(2)

newdf['feedback'].values[newdf['reviews.rating'].values ==5] = 1
newdf['feedback'].values[newdf['reviews.rating'].values <3] = 0
newdf=newdf.dropna()

newdf['posTag'] = newdf.apply(lambda row: nltk.pos_tag(row['preprocessed']), axis=1)
newdf['posTag'].head(2)

"""**Filter Adjectives**"""

def keepAdj(txt):
    newText =[]
    for word in txt:
        if word[1] in ('JJ','JJS','JJR'):
            newText.append(word[0])
    return newText
newdf['keepAdj'] = newdf['posTag'].apply(keepAdj)
newdf['keepAdj'].head(2)

"""**Convert categorical variable into indicator variables**"""

variation_dummies = pd.get_dummies(newdf['name'], drop_first = True) 
variation_dummies.head(2)

"""**Convert Y-target to categorical variable**"""

from keras.utils import to_categorical
target=newdf['reviews.rating'].values
y_target=to_categorical(target)
num_classes=y_target.shape[1]

newdf = pd.concat([newdf, variation_dummies], axis=1)

y_target

"""**Convert Tuple to String**"""

def converTupleStr(tup):
  return ' '.join(tup)
newdf['preprocessedStr'] = newdf['preprocessed'].apply(lambda row: converTupleStr(row) )
newdf['newPreprocessed'] = newdf['preprocessed'].apply(lambda row: converTupleStr(row) )
newdf['newPreprocessed'].head(2) # we can use thise instead of preproceesdStr

## Defining this datafram to use later in the recommendation system 
conRecomDf = newdf.groupby(['name'], as_index = False).agg({'preprocessedStr': ' '.join})
conRecomDf.head(2)

newdf.drop(['name'], axis=1, inplace=True)

"""**Vectorizing vocabulary**"""

from sklearn.feature_extraction.text import CountVectorizer

vectorizer = CountVectorizer()
newdf_countvectorizer = vectorizer.fit_transform(newdf['newPreprocessed']) # The text has to be cleaned first.
newdf_countvectorizer.shape
print(vectorizer.get_feature_names())
print(len(vectorizer.get_feature_names()))

"""**Display TSNE**"""

from yellowbrick.text import TSNEVisualizer
from sklearn.feature_extraction.text import TfidfVectorizer

data = newdf['newPreprocessed']
tfidf = TfidfVectorizer()
docs = tfidf.fit_transform(data)
labels = newdf['feedback']

tsne = TSNEVisualizer()
tsne.fit_transform(docs, labels)
tsne.poof() 
# show the distribution of negative and positive reviews

newdf.drop(['reviews.text'], axis=1, inplace=True) 
reviews = pd.DataFrame(newdf_countvectorizer.toarray())
newdf.head(1)

"""**Set Feature X and Target Y**"""

newdf.reset_index(drop=True, inplace=True)
newdf = pd.concat([newdf, reviews], axis=1)
X = newdf.drop(['reviews.rating','feedback','preprocessed','preprocessedStr','preprocessedStr','newPreprocessed','keepAdj','posTag'],axis=1)
y = newdf['feedback']

"""*Split Test & Train Set*"""

X = np.asarray(X).astype(np.float32) #fixed type to float as tensor doesn't allow int
y = np.asarray(y).astype(np.float32)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20, random_state=5)

"""**Model 1 : Neural Network_V1**

> *This model predicts binary value either Positive or Negative*


"""

import tensorflow_addons as tfa


ANN_classifier = tf.keras.models.Sequential()
#2 layers are used. relu= rectified  something
ANN_classifier.add(tf.keras.layers.Dense(units=400, activation='relu', input_shape=(X_train.shape[1] ,   )))
#Change input shape when needed.
ANN_classifier.add(tf.keras.layers.Dense(units=400, activation='relu'))
##sigmoid 0 or 1, can we imporeve it as percentage instead?
ANN_classifier.add(tf.keras.layers.Dense(units=1, activation='sigmoid'))
ANN_classifier.summary()
ANN_classifier.compile(optimizer='Adam', loss='binary_crossentropy',metrics=[tfa.metrics.F1Score(num_classes=2, average="micro")])

epochs_hist = ANN_classifier.fit(X_train, y_train, epochs = 10)

"""**Learning Curve for each epoch**"""

# Create count of the number of epochs
epoch_count = range(1, len(epochs_hist.history['loss']) + 1)
# Visualize learning curve. Here learning curve is not ideal. It should be much smoother as it decreases.
#As mentioned before, altering different hyper parameters especially learning rate can have a positive impact
#on accuracy and learning curve.
plt.plot(epoch_count, epochs_hist.history['loss'], 'r--')
plt.legend(['Training Loss', 'Validation Loss'])
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.show()

"""**Accuracy & Loss on Test Set**"""

ANN_classifier.evaluate(X_test, y_test)

"""**Model 1 : Neural Network_V2**

> *This model predicts sentimental score from 1-5*


"""

#seconds types of data splitting to get score 0-5

X_train2, X_test2, y_train2, y_test2=train_test_split(X,y_target,test_size=0.2,stratify=y_target)

ANN_classifier = tf.keras.models.Sequential()
#2 layers are used. relu= rectified  something
ANN_classifier.add(tf.keras.layers.Dense(units=400, activation='relu', input_shape=(X_train.shape[1], )))
ANN_classifier.add(tf.keras.layers.Dense(units=400, activation='relu'))
##sigmoid 0 or 1, can we imporeve it as percentage instead?
ANN_classifier.add(tf.keras.layers.Dense(num_classes,activation='softmax'))
ANN_classifier.summary()
ANN_classifier.compile(optimizer='Adam', loss='binary_crossentropy', metrics = ['accuracy'])
epochs_hist = ANN_classifier.fit(X_train2, y_train2, epochs = 10)

"""**Learning Curve for each epoch**"""

# Create count of the number of epochs
epoch_count = range(1, len(epochs_hist.history['loss']) + 1)

# Visualize learning curve. Here learning curve is not ideal. It should be much smoother as it decreases.
#As mentioned before, altering different hyper parameters especially learning rate can have a positive impact
#on accuracy and learning curve.
plt.plot(epoch_count, epochs_hist.history['loss'], 'r--')
plt.legend(['Training Loss', 'Validation Loss'])
plt.xlabel('Epoch')
plt.ylabel('Loss')
plt.show()

"""**Accuracy & Loss on Test Set**"""

ANN_classifier.evaluate(X_test2, y_test2)

from tqdm import tqdm
unique_words = set()
len_max = 0

for sent in tqdm(X_train):
    
    unique_words.update(sent)
    
    if(len_max<len(sent)):
        len_max = len(sent)
        
#length of the list of unique_words gives the no of unique words
print(len(list(unique_words)))
print(len_max)

"""**RNN - LSTM**"""

from keras.layers import Dense,Dropout,Embedding,LSTM
from keras.callbacks import EarlyStopping
from keras.losses import categorical_crossentropy
from keras.optimizers import Adam
from keras.models import Sequential

early_stopping = EarlyStopping(min_delta = 0.001, mode = 'max', monitor='val_acc', patience = 2)
callback = [early_stopping]

model=Sequential()
model.add(Embedding(len(list(unique_words)),50,input_length=len_max))
model.add(LSTM(16,dropout=0.5, recurrent_dropout=0.5,return_sequences=True))
model.add(LSTM(8,dropout=0.5, recurrent_dropout=0.5,return_sequences=False))
model.add(Dense(100,activation='relu'))
model.add(Dropout(0.5))
model.add(Dense(num_classes,activation='softmax'))
model.compile(loss='categorical_crossentropy',optimizer=Adam(lr=0.005),metrics=['accuracy'])
model.summary()

history=model.fit(X_train2, y_train2, epochs=6, batch_size=256, verbose=1, callbacks=callback)

"""**CNN**"""

from keras.layers import Conv1D, Conv2D, Convolution1D, MaxPooling1D, SeparableConv1D, SpatialDropout1D, \
    GlobalAvgPool1D, GlobalMaxPool1D, GlobalMaxPooling1D 
from keras.layers import Input, Add, concatenate, Dense, Activation, BatchNormalization, Dropout, Flatten
model = Sequential()
model.add(Embedding(len(list(unique_words)),50,input_length=len_max))
model.add(Conv1D(16, 3, padding='valid', activation='relu', strides=1))
model.add(GlobalMaxPooling1D())


model.add(Dropout(0.5))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(2048, activation='relu'))

model.add(Dropout(0.5))
model.add(BatchNormalization())
model.add(Dropout(0.5))

model.add(Dense(num_classes, activation='softmax'))
model.compile(loss='categorical_crossentropy',optimizer=Adam(lr=0.005),metrics=['accuracy'])
model.summary()

history=model.fit(X_train2, y_train2, epochs=6, batch_size=256, verbose=1, callbacks=callback)

"""**Plot Confusion Matrix**"""

from sklearn.metrics import plot_confusion_matrix

def plotMatrix(title, model, pred, y_test):
  labels = [0, 1]
  cm = confusion_matrix(y_test, pred, labels)
  print(cm)
  fig = plt.figure()
  ax = fig.add_subplot(111)
  cax = ax.matshow(cm)
  plt.title('Confusion matrix of the ' + title)
  fig.colorbar(cax)
  ax.set_xticklabels([''] + labels)
  ax.set_yticklabels([''] + labels)
  plt.xlabel('Predicted')
  plt.ylabel('True')
  plt.show()

# separate test and train data 
X_train2, X_test2, y_train2, y_test2=train_test_split(X,y_target,test_size=0.2,stratify=y_target)

"""**Gaussian Naive Bayes**


"""

gnb = GaussianNB()
gnb.fit(X_train2, np.argmax(y_train2,axis=1))
pred_gnb = gnb.predict(X_test2)
gnb.score(X_test2, np.argmax(y_test2,axis=1))
plotMatrix("Gaussian Naive Bayes",gnb, pred_gnb, np.argmax(y_test2,axis=1) )

"""**Model 2 : SVM**"""

from sklearn import svm
svmModel = svm.SVC(kernel='linear')
svmModel.fit(X_train2, np.argmax(y_train2,axis=1))
svmPredict = svmModel.predict(X_test2)
svmModel.score(X_test2, np.argmax(y_test2,axis=1))

plotMatrix("SVM",svmModel, svmPredict, np.argmax(y_test2,axis=1) )

"""**Model 3 : Random Forest**"""

from sklearn.ensemble import RandomForestClassifier
RFModel = RandomForestClassifier(max_depth=10, random_state=1)
RFModel.fit(X_train2, np.argmax(y_train2,axis=1))
RFPredict = RFModel.predict(X_test2)
RFModel.score(X_test2, np.argmax(y_test2,axis=1))

plotMatrix("Random Forest",RFModel, RFPredict, np.argmax(y_test2,axis=1) )

from sklearn.metrics import confusion_matrix, classification_report
confusion_matrix = confusion_matrix(np.argmax(y_test2,axis=1), pred_gnb)
classification_report = classification_report(np.argmax(y_test2,axis=1), pred_gnb, output_dict=True)
classification_report

"""**Model 3 : Linear Regression**



> The idea is to apply simple linear regression to the dataset and then to check least square error. If the least square error shows high accuracy, it implies the dataset being linear in nature, else dataset is non-linear.


"""

from sklearn.linear_model import LinearRegression
regressor = LinearRegression().fit(X_train2, np.argmax(y_train2,axis=1))
# Checking the accuracy
from sklearn.metrics import r2_score
print(r2_score(regressor.predict(X_train2), np.argmax(y_train2,axis=1)))

"""**Recommendation System**


> Calculation based on the IMDB formula


"""

#Recommendation System https://www.kaggle.com/ibtesama/getting-started-with-a-movie-recommendation-system
c=dfNew['reviews.rating'].mean()
#dfNew['name','reviews.rating'].groupby('name').mean()
average_score=dfNew[['name','reviews.rating']].groupby('name').mean()
vote_count=dfNew[['name','reviews.rating']].groupby('name').count()
m=vote_count.quantile(0.5)
C=average_score.mean() #C is the mean vote across the whole report
def weighted_rating(x, m=m, C=C):
    v = x['Count_Vote']
    R = x['Avg_Rate']
    # Calculation based on the IMDB formula
    return (v/(v+m) * R) + (m/(m+v) * C)
m

"""**Calculating Score for Each Hotel**


> The higher the score, The higher the positiveness


"""

NewdataSet=dfNew[['city','name','reviews.rating']]
average_score=average_score.rename(columns={"reviews.rating": "Avg_Rate"})
vote_count=vote_count.rename(columns={"reviews.rating": "Count_Vote"})
Data=  pd.concat([average_score, vote_count], axis=1)
Data.reset_index(inplace=True)
Data['Count_Vote'] = np.asarray(Data['Count_Vote']).astype(np.float64)
#q_movies = [Data['Count_Vote'] >= m]
#q_movies
Data = Data[Data['Count_Vote']	 >=20]
Data['score'] = Data.apply(weighted_rating, axis=1)
Data

"""**Filter the Score and Label Sentiment**


> Higher than 2 => Positive

> Less than 2 => Negative




"""

Data = Data.sort_values('score', ascending=False)
Data.head(10) #top 10 Demographic Filtering 
def f2(row):
    '''This function returns sentiment value based on the overall ratings from the user'''
    if row['Avg_Rate'] <2 :
        val = 'Negative'
    elif row['Avg_Rate'] > 4.0:
        val = 'Positive'
    elif row['Avg_Rate'] >2 or row['Avg_Rate']<4 :
        val = 'Neutral'
    else:
        val = -1
    return val
Data['sentiment'] = Data.apply(f2, axis=1)
Data

"""**Content Based Recommendation System**

The idea is to suggest similar items based on a particular item, here we used the cosine similarity on the reviews of the hotels and recommend the hotel based on the similarity of their reviews
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel

tfidf = TfidfVectorizer()

conRecomDf['preprocessedStr'] = conRecomDf['preprocessedStr'].fillna('')
tfidf_matrix = tfidf.fit_transform(conRecomDf['preprocessedStr'])

# Computing cosine similarity 
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
indices = pd.Series(conRecomDf.index, index=conRecomDf['name']).drop_duplicates()

# Function that takes in hotel title as input and outputs most similar hotels 
def get_recommendations(name, cosine_sim=cosine_sim):
    idx = indices[name]

    # pairwsie similarity scores 
    sim_scores = list(enumerate(cosine_sim[idx]))

    # Sort based on the similarity scores and get 5 most scores
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:6]
    # get the indices 
    hotel_indices = [i[0] for i in sim_scores]

    return conRecomDf['name'].iloc[hotel_indices]

get_recommendations('Ambassadors Inn and Suites')



# Commented out IPython magic to ensure Python compatibility.

# %matplotlib inline

#plot layout
plt.rcParams.update({'font.size': 18})
rcParams['figure.figsize'] = 16,9

# Creating dataframe and removing 0 helpfulrate records
senti_help= pd.DataFrame(Data, columns = ['sentiment', 'Avg_Rate'])
senti_help = senti_help[senti_help['Avg_Rate'] != 0.00] 

#Plotting phase
sns.violinplot( x=senti_help["sentiment"], y=senti_help["Avg_Rate"])
plt.title('Sentiment vs score')
plt.xlabel('Sentiment categories')
plt.ylabel('score rate')
plt.show()

#plotting
data=dfNew[['city','name','reviews.rating','year','Month','time','preprocessed']]
data['preprocessed'] = data['preprocessed'].apply(lambda row: converTupleStr(row) )
data

def f(row):
    '''This function returns sentiment value based on the overall ratings from the user'''
    if row['reviews.rating'] == 3.0:
        val = 'Neutral'
    elif row['reviews.rating'] == 1.0 or row['reviews.rating'] == 2.0:
        val = 'Negative'
    elif row['reviews.rating'] == 4.0 or row['reviews.rating'] == 5.0:
        val = 'Positive'
    else:
        val = -1
    return val

data['reviews.rating'] = np.asarray(data['reviews.rating']).astype(np.float64)
data['sentiment'] = data.apply(f, axis=1)

data['sentiment'].value_counts()
data



"""**Analysis By Year**

"""

data.groupby(['year','sentiment'])['sentiment'].count().unstack().plot(legend=True)
plt.title('Year and Sentiment count')
plt.xlabel('Year')
plt.ylabel('Sentiment count')
plt.show()

"""**Analysis By Month**"""

#Creating a dataframe
day=pd.DataFrame(data.groupby('Month')['preprocessed'].count()).reset_index()
day['Month']=day['Month'].astype('int64')
day.sort_values(by=['Month'])

#Plotting the graph
sns.barplot(x="Month", y="preprocessed", data=day)
plt.title('Month vs Reviews count')
plt.xlabel('Month')
plt.ylabel('Reviews count')
plt.show()

data['polarity'] = data['preprocessed'].map(lambda text: TextBlob(text).sentiment.polarity)
data['review_len'] = data['preprocessed'].astype(str).apply(len)
data['word_count'] = data['preprocessed'].apply(lambda x: len(str(x).split()))
data

"""**Frequency Distribution**"""

from wordcloud import WordCloud,STOPWORDS
from collections import defaultdict
#Filtering data
review_pos = data[data["sentiment"]=='Positive'].dropna()
review_neu = data[data["sentiment"]=='Neutral'].dropna()
review_neg = data[data["sentiment"]=='Negative'].dropna()

## custom function for ngram generation ##
def generate_ngrams(text, n_gram=1):
    token = [token for token in text.lower().split(" ") if token != "" if token not in STOPWORDS]
    ngrams = zip(*[token[i:] for i in range(n_gram)])
    return [" ".join(ngram) for ngram in ngrams]

## custom function for horizontal bar chart ##
def horizontal_bar_chart(df, color):
    trace = go.Bar(
        y=df["word"].values[::-1],
        x=df["wordcount"].values[::-1],
        showlegend=False,
        orientation = 'h',
        marker=dict(
            color=color,
        ),
    )
    return trace
remove =['room','hotel','stay']
## Get the bar chart from positive reviews ##
freq_dict = defaultdict(int)
for sent in review_pos["preprocessed"]:
    for word in generate_ngrams(sent):
        if word not in remove:
            freq_dict[word] += 1
fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
fd_sorted.columns = ["word", "wordcount"]
trace0 = horizontal_bar_chart(fd_sorted.head(25), 'green')

## Get the bar chart from neutral reviews ##
freq_dict = defaultdict(int)
for sent in review_neu["preprocessed"]:
    for word in generate_ngrams(sent):
        if word not in remove:
            freq_dict[word] += 1
fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
fd_sorted.columns = ["word", "wordcount"]
trace1 = horizontal_bar_chart(fd_sorted.head(25), 'grey')

## Get the bar chart from negative reviews ##
freq_dict = defaultdict(int)
for sent in review_neg["preprocessed"]:
    for word in generate_ngrams(sent):
        if word not in remove:
            freq_dict[word] += 1
fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
fd_sorted.columns = ["word", "wordcount"]
trace2 = horizontal_bar_chart(fd_sorted.head(25), 'red')

# Creating two subplots
fig = tools.make_subplots(rows=3, cols=1, vertical_spacing=0.04,
                          subplot_titles=["Frequent words of positive reviews", "Frequent words of neutral reviews",
                                          "Frequent words of negative reviews"])
fig.append_trace(trace0, 1, 1)
fig.append_trace(trace1, 2, 1)
fig.append_trace(trace2, 3, 1)
fig['layout'].update(height=1200, width=900, paper_bgcolor='rgb(233,233,233)', title="Word Count Plots")
iplot(fig, filename='word-plots')

## Get the bar chart from positive reviews ##
freq_dict = defaultdict(int)
for sent in review_pos["preprocessed"]:
    for word in generate_ngrams(sent,2):
        freq_dict[word] += 1
fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
fd_sorted.columns = ["word", "wordcount"]
trace0 = horizontal_bar_chart(fd_sorted.head(25), 'green')

## Get the bar chart from neutral reviews ##
freq_dict = defaultdict(int)
for sent in review_neu["preprocessed"]:
    for word in generate_ngrams(sent,2):
        freq_dict[word] += 1
fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
fd_sorted.columns = ["word", "wordcount"]
trace1 = horizontal_bar_chart(fd_sorted.head(25), 'grey')

## Get the bar chart from negative reviews ##
freq_dict = defaultdict(int)
for sent in review_neg["preprocessed"]:
    for word in generate_ngrams(sent,2):
        freq_dict[word] += 1
fd_sorted = pd.DataFrame(sorted(freq_dict.items(), key=lambda x: x[1])[::-1])
fd_sorted.columns = ["word", "wordcount"]
trace2 = horizontal_bar_chart(fd_sorted.head(25), 'brown')



# Creating two subplots
fig = tools.make_subplots(rows=3, cols=1, vertical_spacing=0.04,horizontal_spacing=0.25,
                          subplot_titles=["Bigram plots of Positive reviews", 
                                          "Bigram plots of Neutral reviews",
                                          "Bigram plots of Negative reviews"
                                          ])
fig.append_trace(trace0, 1, 1)
fig.append_trace(trace1, 2, 1)
fig.append_trace(trace2, 3, 1)


fig['layout'].update(height=1000, width=800, paper_bgcolor='rgb(233,233,233)', title="Bigram Plots")
iplot(fig, filename='word-plots')



text = review_pos["preprocessed"]
wordcloud = WordCloud(
    width = 200,
    height = 100,
    background_color = 'black',
    stopwords = STOPWORDS).generate(str(text))
fig = plt.figure(
    figsize = (40, 30),
    facecolor = 'k',
    edgecolor = 'k')
plt.imshow(wordcloud, interpolation = 'bilinear')
plt.axis('off')
plt.tight_layout(pad=0)
plt.show()

https://www.kaggle.com/benroshan/sentiment-analysis-amazon-reviews





from collections import Counter
def countFreq(text):
    for w in text.split(" "):
        if w not in wordfreq:
            wordfreq[w]=0
        else:
            wordfreq[w]+=1
    
wordfreq = {}
a = newdf['preprocessedStr'].apply(countFreq)
k = Counter(wordfreq)
high = k.most_common(20)
high

# heating map, graph, to present.
# svm *
# frquency, rate,  
#

# we should try this
# https://towardsdatascience.com/building-a-content-based-recommender-system-for-hotels-in-seattle-d724f0a32070

#https://www.kaggle.com/chiranjeevbit/movie-review-prediction
# i tried it with our data and it works to give rate 1-5 but we have to modify it a lot. i think we can improve a lot here too
# I did the first draft for the sentiment. It seems the basic model is working, so I'll check on recommendation system.
#we still have to do
#tokenizer
#cleansing
#prof: You will of course have to try one or more methods for converting a variable-length document into a fixed-length feature representation to use as input to SVM etc.
#different method   -supervised(what we tried so far, and more)
#svm
#neural network(with tensor)
#unsupervised(https://towardsdatascience.com/unsupervised-sentiment-analysis-a38bf1906483)
#with deeplearning (https://towardsdatascience.com/sentiment-analysis-for-text-with-deep-learning-2f0a0c6472b5)
#recommendation system (i think we can try different method too for this )

