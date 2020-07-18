import tensorflow as tf
from tensorflow import keras

from tensorflow.keras.layers import Concatenate, Conv1D, Dense, Dropout, Embedding, GlobalMaxPool1D, Input

from tensorflow.keras.losses import SparseCategoricalCrossentropy
from tensorflow.keras.metrics import SparseCategoricalAccuracy
from tensorflow.keras.models import Model
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import plot_model


class TextCNN(keras.Model):
    def __init__(self, vocab_size, embedding_dim, filter_sizes, num_filters,
                 hidden_dim, dropout_p, num_classes, freeze_embeddings=False):
        super(TextCNN, self).__init__(name="cnn")

        # Embeddings
        self.embedding = Embedding(
            input_dim=vocab_size, output_dim=embedding_dim,
            trainable=not freeze_embeddings)

        # Conv & pool
        self.convs = []
        self.pools = []
        for filter_size in filter_sizes:
            conv = Conv1D(
                filters=num_filters, kernel_size=filter_size,
                padding='same', activation='relu')
            pool = GlobalMaxPool1D(data_format='channels_last')
            self.convs.append(conv)
            self.pools.append(pool)

        # Concatenation
        self.concat = Concatenate(axis=1)

        # FC layers
        self.fc1 = Dense(units=hidden_dim, activation='relu')
        self.dropout = Dropout(rate=dropout_p)
        self.fc2 = Dense(units=num_classes, activation='softmax')

    def call(self, x_in, training=False):
        """Forward pass."""
        # Embed
        x_emb = self.embedding(x_in)

        # Conv & pool
        convs = []
        for i in range(len(self.convs)):
            z = self.convs[i](x_emb)
            z = self.pools[i](z)
            convs.append(z)

        # Concatenate
        z_cat = self.concat(convs)

        # FC
        z = self.fc1(z_cat)
        if training:
            z = self.dropout(z, training=training)
        logits = self.fc2(z)

        return logits

    def compile(self, learning_rate):
        super(TextCNN, self).compile()
        self.optimizer = Adam(lr=learning_rate)
        self.loss_fn = SparseCategoricalCrossentropy()
        self.accuracy_fn = SparseCategoricalAccuracy()

    def train_step(self, batch):
        X, y, _ =  batch

        with tf.GradientTape() as tape:
            y_pred = self.call(X, training=True)
            loss = self.loss_fn(y, y_pred)
            accuracy = self.accuracy_fn(y, y_pred)

        grads = tape.gradient(loss, self.trainable_weights)
        self.optimizer.apply_gradients(zip(grads, self.trainable_weights))

        return {'loss':loss, 'accuracy': accuracy}

    def test_step(self, batch):
        X, y =  batch
        y_pred = self.call(X)
        loss = self.loss_fn(y, y_pred)
        accuracy = self.accuracy_fn(y, y_pred)
        return {'loss':loss, 'accuracy': accuracy}

    def summary(self, input_shape):
        x_in = Input(shape=input_shape, name='X')
        summary = Model(inputs=x_in, outputs=self.call(x_in), name=self.name)
        return summary


class ConvOutputsModel(Model):
    def __init__(self, vocab_size, embedding_dim,
                 filter_sizes, num_filters):
        super(ConvOutputsModel, self).__init__()

        # Embeddings
        self.embedding = Embedding(input_dim=vocab_size,
                                   output_dim=embedding_dim)

        # Conv & pool
        self.convs = []
        for filter_size in filter_sizes:
            conv = Conv1D(filters=num_filters, kernel_size=filter_size,
                          padding='same', activation='relu')
            self.convs.append(conv)

    def call(self, x_in, training=False):
        """Forward pass."""
        # Embed
        x_emb = self.embedding(x_in)

        # Conv
        convs = []
        for i in range(len(self.convs)):
            z = self.convs[i](x_emb)
            convs.append(z)

        return convs

    def summary(self, input_shape):
        x_in = Input(shape=input_shape, name='X')
        summary = Model(inputs=x_in, outputs=self.call(x_in), name=self.name)
        return summary