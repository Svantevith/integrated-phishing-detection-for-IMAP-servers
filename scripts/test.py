import tensorflow as tf
from classes.LSTMClassifier import LSTMClassifier

lstm = LSTMClassifier()
data = tf.data.Dataset.from_tensors(['sdsadsa', 'dsadsaas'])
lstm.compute_vocabulary(data)
res = lstm.call(tf.convert_to_tensor(['dsdsads']))
print(type(res))