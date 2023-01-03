import numpy as np
import torch
import torch.nn as nn
from sklearn.base import BaseEstimator, TransformerMixin


class FeedForwardModel(nn.Module):
    """
    The internal model for the ForwardFinetuner
    """

    def __init__(self, input_dim, hidden_dim, output_dim):
        super(FeedForwardModel, self).__init__()
        self.hidden = nn.Linear(input_dim, hidden_dim)
        self.relu = nn.ReLU()
        self.linear = nn.Linear(hidden_dim, output_dim)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        """Runs the forward pass"""
        return self.sigmoid(self.linear(self.embed(x)))

    def embed(self, x):
        """Runs the embedding pass"""
        return self.sigmoid(self.hidden(x))


class ForwardFinetuner(BaseEstimator, TransformerMixin):
    """
    Create a feed forward model to finetune the embeddings towards a class.

    Arguments:
        hidden_dim: The size of the hidden layer
        n_epochs: The number of epochs to run the optimiser for
        learning_rate: The learning rate of the feed forward model
    """

    def __init__(self, hidden_dim=50, n_epochs=500, learning_rate=0.01) -> None:
        self.hidden_dim = hidden_dim
        self.n_epochs = n_epochs
        self.learning_rate = learning_rate

    def fit(self, X, y):
        """Fits the finetuner."""
        return self.partial_fit(X, y, classes=np.unique(y))

    def partial_fit(self, X, y, classes=None):
        """Fits the finetuner using the partial_fit API."""
        if not hasattr(self, "_classes"):
            if classes is None:
                raise ValueError("`classes` must be provided for partial_fit")
            self._classes = classes
        # Create a model if it does not exist yet.
        if not hasattr(self, "_model"):
            self._model = FeedForwardModel(
                X.shape[1], self.hidden_dim, len(self._classes)
            )
            self._optimizer = torch.optim.Adam(
                self._model.parameters(), lr=self.learning_rate
            )
            self._criterion = nn.CrossEntropyLoss()

        torch_X = torch.from_numpy(X).detach().float()
        torch_y = torch.from_numpy(y).detach()

        for _ in range(self.n_epochs):
            self._optimizer.zero_grad()
            out = self._model(torch_X)
            loss = self._criterion(out, torch_y)
            loss.backward()
            self._optimizer.step()

        return self

    def transform(self, X, y=None):
        """Transforms the data according to the sklearn api by using the hidden layer."""
        Xt = torch.from_numpy(X).float().detach()
        return self._model.embed(Xt).detach().numpy()
