import numpy as np

class Stochastic_matrix:
    """A square matrix where the sum of the elements of every row is equal to 1.
    In this context, the element at row i and column j is the probability of
    the object j to have randomized appearence i, and the sum of any row is indeed equal
    to 1 because, in Nethack, a randomized appearence can only be used by one object.
    If we consider the fact that an object can only have one appearence, then we also
    need the sum of the elemets of every column to be equal to one, thus a bistochastic matrix
    """
    def __init__(self, objs, aboundance):
        """Make a new nxn stochastic matrix where all elements are equal to 1/n"""
        n = len(objs)
        assert n == len(aboundance)
        self.objects = objs
        # appearences are added with self.found, starting with empty list
        self.appearences = []
        # this is used by self.found to update probabilities
        self.aboundance = aboundance
        # this is used by self.get_bistochastic to approximate(and remember) a bistochastic matrix
        self.probabilities = np.ones((n, n))/n
        self.c, self.r = np.ones((2, n))

    def reset(self):
        """Set all elements to their initial value"""
        self.probabilities[:] = 1/len(self.objects)

    def add_appearence_if_missing(self, appearence):
        """If appearence is new, add it to the list"""
        if appearence not in self.appearences:
            self.appearences.append(appearence)
            assert len(self.appearences) <= len(self.objects)

    def get_bistochastic(self, max_it, tolerance):
        """Approximate a new bistochastic matrix by applying the Sinkhorn-Knopp algorithm"""
        def bis_mse(mat):
            """Return the mean square error, where error is the difference between 1 and the sum on the rows and the columns of the given matrix"""
            return ((np.concatenate(
                (mat.sum(axis=0),
                 mat.sum(axis=1))
            ) - 1)**2).mean()
        b = self.probabilities * self.c * self.r.reshape(-1, 1)
        # should I reset or keep the vectors self.c and self.r?
        if bis_mse(b) > bis_mse(self.probabilities):
            self.c[:] = self.r[:] = 1  # reset
        for i in range(max_it):
            # update c to normalize columns
            self.c = 1/(self.r @ self.probabilities)
            # update r to normalize rows
            self.r = 1/(self.probabilities @ self.c)
            b[:] = self.probabilities * self.c * self.r.reshape(-1, 1)
            if bis_mse(b) <= tolerance:
                return (b, i+1)
        return (None, max_it)

    def get_prob(self, mat, appearence, obj):
        """Get the probability that obj has the given appearence, given the probability matrix"""
        assert obj in self.objects
        if appearence not in self.appearences:  # not found yet
            assert len(self.appearences) < len(self.objects)
            return mat[-1, self.objects.index(obj)]
        return mat[self.appearences.index(appearence),
                   self.objects.index(obj)]

    def get_possible_objects(self, mat, appearence):
        """Get a list of pairs (p, object) such that object has p probability to have the given appearence.
        The objects with higer probability are at the beginning of the list.
        For the probabilities to be accurate, the given matrix must be bistochastic"""
        return sorted(([self.get_prob(mat, appearence, obj), obj]
                      for obj in self.objects), reverse=True)

    def is_not(self, appearence, obj):
        """Set the probability that object has the given appearence to 0"""
        assert obj in self.objects
        self.add_appearence_if_missing(appearence)
        row = self.probabilities[self.appearences.index(appearence)]
        row[self.objects.index(obj)] = 0
        row /= row.sum()

    def known(self, appearence, obj):
        """Set the probability that object has the given appearence to 1"""
        assert obj in self.objects
        self.add_appearence_if_missing(appearence)
        self.probabilities[self.appearences.index(appearence), :] = 0
        self.probabilities[self.appearences.index(appearence),
                           self.objects.index(obj)] = 1

    def found(self, appearence):
        """By finding an object with given appearence, the probabilities associated with this appearence must be updated considering the aboundance of the possible objects"""
        self.add_appearence_if_missing(appearence)
        row = self.probabilities[self.appearences.index(appearence)]
        row *= self.aboundance
        row /= row.sum()
