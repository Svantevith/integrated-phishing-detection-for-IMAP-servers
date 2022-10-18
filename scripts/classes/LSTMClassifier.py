import tensorflow as tf
from tensorflow.python.framework.ops import EagerTensor
from keras import Model
from keras.layers import Dense, Embedding, LSTM, SpatialDropout1D, TextVectorization, Input, Dropout
from keras.engine.functional import Functional

class LSTMClassifier(Model):
    """
    LSTM Model for multi-category classification.

    Attributes
    ----------
    n_classes : int
        Number of output categories
    vocab_size : int
        Vocabulary size. By default 50 000.
    max_seq_len : int 
        Max number of words for each sequence. By default 250.
    embed_dim : int 
        Max embedding size. By default 100.
    n_grams : int 
        Number of tokens to embed into ngrams vector. By default 2.
    input_layer : tf.keras.layers.Input
        Input layer.
    vectorize_layer : tf.keras.layers.TextVectorization
        Layer to transfer text into vocabulary indices.
    embedding_layer : tf.keras.layers.Embedding
        Layer to map vocabulary indices into dense vectors.
    spatial_dropout : tf.keras.layers.SpatialDropout1D
        Layer to promote independence between feature maps.
    lstm_[n] : tf.keras.layers.LSTM
        Long Short-Term Memory layer(s) effectively memorize important embeddings.
    dense_[n] : tf.keras.layers.Dense
        Dense layer(s) increase the model's capacity to capture complex relationships.
    dropout_[n] : tf.keras.layers.Dropout
        Follows each Dense layer and regulates the network, keeping it far from any bias.
    classifier : tf.keras.layers.Dense
        Output layer.

    Methods
    -------
    handle_starttag(tag, attrs)
        Append new opening tags and attributes.

    handle_endtag(self, tag)
        Append new closing tags.
    
    contains_content_type(content_type)
        Return boolean flag indicating MIME content-type presence. 
    """ 
    
    def __init__(self, n_classes: int = 2, vocab_size: int = 50000, max_seq_len: int = 250, embed_dim: int = 100, n_grams: int = 2) -> None:
        """
        Constructs all the necessary attributes for the custom Model object.

        Parameters
        ----------
        n_classes : int, optional
            Number of output categories. Default is 2.
        vocab_size : int, optional
            Vocabulary size. Default is 50 000.
        max_seq_len : int, optional 
            Max number of words for each sequence. Default is 250.
        embed_dim : int, optional 
            Max embedding size. Default is 100.
        n_grams : int, optional 
            Number of tokens to embed into ngrams vector. Default is 2.
        """
        # Call parent constructor
        super(LSTMClassifier, self).__init__()
        
        # Assign variables to parameters
        self.n_classes = n_classes
        self.vocab_size = vocab_size
        self.max_seq_len = max_seq_len
        self.embed_dim = embed_dim
        self.n_grams = n_grams      
        
        # Define layers
        self.input_layer = Input(
            name='inputs', 
            shape=(1,), 
            dtype=tf.string
        )
        self.vectorize_layer = TextVectorization(
            max_tokens=self.vocab_size, 
            output_mode='int', 
            output_sequence_length=self.max_seq_len, 
            ngrams=self.n_grams,
            pad_to_max_tokens=True,
            name='vectorization_layer'
        )
        self.embedding_layer = Embedding(
            input_dim=self.vocab_size + 1, 
            output_dim=self.embed_dim,
            name='embedding_layer'
        )
        self.spatial_dropout = SpatialDropout1D(rate=0.2)
        self.lstm_1 = LSTM(
            units=128, 
            dropout=0.2, 
            recurrent_dropout=0.2, 
            name='lstm_layer_01'
        )
        self.dense_1 = Dense(
            units=32, 
            activation='relu',
            name='dense_layer_01'
        )
        self.dropout_1 = Dropout(0.5)
        self.classifier = Dense(
            units=self.n_classes, 
            activation='softmax', 
            name='outputs'
        )
    
    def call(self, inputs) -> EagerTensor:
        """
        Build a new computational graph from the provided inputs and return the outputs as tensors.

        Parameters
        ----------
        inputs : {tf.Tensor, List[tf.Tensor], Tuple[tf.Tensor], Dict[str, tf.Tensor]}
            The input(s) of the model.
        
        Returns
        -------
        outputs : {tf.Tensor, List[tf.Tensor]}
            The output(s) of the model.

        """
        # TextVectorization layer is used to normalize, split, and map strings to integers (set `output_mode` to `int`), thus needs to be instantiated before calling the model.
        # This layer transforms input document into a tensor of shape (batch_size, max_len) containing vocab indices.
        # Explicitly set maximum sequence length, as the LSTM layers do not support ragged sequences.
        # These layers are non-trainable, thus their state (vocabulary) must be set before training.
        # The vocabulary for that layer must be either supplied on construction (precomputed constant) or learned via adapt().
        # Furthermore, TextVectorization layer uses an underlying StringLookup layer that also needs to be initialized beforehand. 
        # Otherwise, FailedPreconditionError: Table not initialized exception is raised.
        x = self.vectorize_layer(inputs)

        # Embedding layer is mapping those vocab indices into a space of dimensionality (embedding_dim,). 
        # Note that we're using max_features + 1 here, since there's an OOV token that is added to the vocabulary in vectorize_layer.
        x = self.embedding_layer(x)

        # SpatialDropout1D performs variational dropout in NLP models.
        # It promotes the independence between single-dimensional feature maps instead of individual elements.
        x = self.spatial_dropout(x)

        # LSTM effectively memorizes important multiple word-level embeddings referring to a particular category.
        # While using multiple LSTM layers, the preceeding LSTM layer needs to return sequences.
        # Then, these sequences are passed as input to the next LSTM layer.
        x = self.lstm_1(x)

        # Following Dense layers increase the model's capacity to capture complex relationships.
        # A dropout layer is used for regulating the network and keeping it as away as possible from any bias.
        x = self.dense_1(x)
        x = self.dropout_1(x)

        # The output Dense layer with a softmax activation function returns prediction probability for each category.
        return self.classifier(x)

    def build_graph(self) -> Functional:
        """
        Helper function to get and plot the model summary information conveniently.
        Graphs are used by tf.functions to represent the function's computations. Each graph contains:
            - Set of tf.Operation objects, which represent units of computation
            - Set of tf.Tensor objects, which represent the units of data that flow between operations.

        Returns
        -------
        graph : keras.engine.functional.Functional
            Model architecture.

        Usage
        ----- 
        View model summary
            LSTMClassifier().build_graph().summary()
        
        Visualize the model graph
            tf.keras.utils.plot_model(
                LSTMClassifier().build_graph(),
                show_shapes=True,
                show_dtype=True,
                show_layer_names=True,
                rankdir="TB",
            )
        """
        x = self.input_layer
        return Model(inputs=x, outputs=self.call(x))

    def compute_vocabulary(self, text_data, batch_size: int = None, steps: int = None) -> None:
        """
        Computes a vocabulary of string terms from tokens in a dataset.

        Parameters
        ----------
        text_data : {tf.data.Dataset, np.ndarray}	
            Textual data to compute the vocabulary on.
        batch_size : int, optional
            Number of samples per state update. Supported with numpy array inputs only. Default is 32.  
        steps : int, optional 
            Total number of steps (batches of samples). Supported with tensorflow Dataset inputs only. Default is None. 

        Usage
        -----
        It is necessary to supply vocabulary to the TextVectorization layer, whenever a model is instantiated (before fitting).
        Input dataset can be batched to set the number of samples per state update.
        """
        self.vectorize_layer.adapt(text_data, batch_size, steps)
