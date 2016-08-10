# -*- coding:utf-8 -*-

from __future__ import print_function
from __future__ import division

from keras.layers import Input, LSTM
from keras.layers.core import RepeatVector
from keras.models import Model
from keras.optimizers import Adam
import os
import json
import datetime
import numpy as np
import data_helpers
import tensorflow as tf
import keras.backend.tensorflow_backend as KTF
import logging

logging.basicConfig(filename='all_results.log',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.DEBUG)

lg = logging.getLogger("ConsoleLogger")
lg.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
ch.setFormatter(formatter)
lg.addHandler(ch)


def model(maxlen, vocab_size, latent_dim=50):
    """
        Simple autoencoder for sequences
    """

    input_dim = vocab_size
    timesteps = maxlen

    lg.info("input_dim " + str(vocab_size) + " latent_dim " + str(latent_dim) + " timesteps " + str(timesteps))

    inputs = Input(shape=(timesteps, input_dim))

    lg.info("Input set")

    # takes time :[
    encoded = LSTM(output_dim=latent_dim)(inputs)

    lg.info("Encoder set")

    decoded = RepeatVector(timesteps)(encoded)

    lg.info("Repeated embedding added")

    # takes time :[
    decoded = LSTM(input_dim, return_sequences=True)(decoded)

    lg.info("Decoder added")

    sequence_autoencoder = Model(inputs, decoded)

    lg.info("Autoencoder brought together as a model")

    adam = Adam()

    lg.info("Adam optimizer created")
    lg.info("Model constructed, compiling now...")

    sequence_autoencoder.compile(loss='categorical_crossentropy', optimizer=adam)

    lg.info("Model compiled.")

    return sequence_autoencoder


def get_session(gpu_fraction=0.2):
    """
        Assume that you have 6GB of GPU memory and want to allocate ~2GB
    """

    num_threads = os.environ.get('OMP_NUM_THREADS')
    gpu_options = tf.GPUOptions(per_process_gpu_memory_fraction=gpu_fraction)

    if num_threads:
        return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options, intra_op_parallelism_threads=num_threads))
    else:
        return tf.Session(config=tf.ConfigProto(gpu_options=gpu_options))


# for reproducibility
np.random.seed(123)
KTF.set_session(get_session())

# set parameters:
subset = None

# Whether to save model parameters
save = True
model_name_path = 'params/lstm_dumb_model.json'
model_weights_path = 'params/lstm_dumb_model_weights.h5'

# Maximum length. Longer gets chopped. Shorter gets padded.
maxlen = 700

# Compile/fit params
batch_size = 80
nb_epoch = 3

lg.info('Loading data...')
# Expect x to be a list of sentences. Y to be a one-hot encoding of the categories.
# (xt, yt), (x_test, y_test) = data_helpers.load_restoclub_data("data_test")
(xt, yt), (x_test, y_test) = data_helpers.load_embedding_data()

lg.info('Creating vocab...')
vocab, reverse_vocab, vocab_size, check = data_helpers.create_vocab_set()

lg.info('Vocabulary: ' + ",".join(vocab))
# test_data = data_helpers.encode_data(x_test, maxlen, vocab, vocab_size, check)

lg.info('Build model...')
dumb_model = model(maxlen, vocab_size)

lg.info('Fit model...')
initial = datetime.datetime.now()

for e in range(nb_epoch):

    xi, yi = data_helpers.shuffle_matrix(xt, yt)
    xi_test, yi_test = data_helpers.shuffle_matrix(x_test, y_test)
    print(xi_test)

    if subset:
        batches = data_helpers.mini_batch_generator(xi[:subset],
                                                    vocab, vocab_size, check,
                                                    maxlen, batch_size=batch_size)
    else:
        batches = data_helpers.mini_batch_generator(xi, vocab, vocab_size,
                                                    check, maxlen, batch_size=batch_size)

    test_batches = data_helpers.mini_batch_generator(xi_test, vocab,
                                                     vocab_size, check, maxlen,
                                                     batch_size=batch_size)

    loss = 0.0
    step = 1
    start = datetime.datetime.now()
    lg.info('Epoch: {}'.format(e))

    for x_train, _ in batches:

        print(x_train)

        f = dumb_model.train_on_batch(x_train, x_train)
        loss += f
        loss_avg = loss / step

        if step % 100 == 0:
            lg.info('  Step: {}'.format(step))
            lg.info('\tLoss: {}.'.format(loss_avg))
        step += 1

    test_loss = 0.0
    test_loss_avg = 0.0
    test_step = 1

    for x_test_batch, y_test_batch in test_batches:
        f_ev = dumb_model.test_on_batch(x_test_batch, x_test_batch)
        test_loss += f_ev
        test_loss_avg = test_loss / test_step
        test_step += 1

    stop = datetime.datetime.now()
    e_elap = stop - start
    t_elap = stop - initial
    lg.info('Epoch {}. Loss: {}.\nEpoch time: {}. Total time: {}\n'.format(e, test_loss_avg, e_elap, t_elap))

if save:
    lg.info('Saving model params...')
    json_string = dumb_model.to_json()

    with open(model_name_path, 'w') as f:
        json.dump(json_string, f, ensure_ascii=False)

    dumb_model.save_weights(model_weights_path, overwrite=True)
