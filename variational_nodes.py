
from __future__ import division
import scipy as s

from nodes import *
from distributions import *
import pdb


"""
This module is used to define Nodes that undergo variational bayesian inference.

Variational nodes have the following main variables:
    Important methods:
    - precompute: precompute some terms to speed up the calculations
    - calculateELBO: calculate evidence lower bound using current estimates of expectations/params
    - getParameters: return current parameters
    - getExpectations: return current expectations
    - update: general update function that calls the following two methods:
        - updateParameters: update parameters using current estimates of expectations
        - updateExpectations: update expectations using current estimates of parameters

    Important attributes:
    - markov_blanket: dictionary that defines the set of nodes that are in the markov blanket of the current node
    - Q: an instance of Distribution() which contains the specification of the variational distribution
    - P: an instance of Distribution() which contains the specification of the prior distribution
    - dim: dimensionality of the node
"""


###########################################
## General classes for variational nodes ##
###########################################

class Variational_Node(Node):
    """
    Abstract class for a multi-view variational node in a Bayesian probabilistic model.
    Variational nodes can be observed or unobserved
    """
    def __init__(self, dim):
        Node.__init__(self,dim)
    def calculateELBO(self):
        # General function to calculate the ELBO of the node
        return 0.
    def updateExpectations(self):
        # General function to update expectations of the Q distribution
        pass
    def getExpectation(self):
        # General function to get the expectated value of the Q distribution
        pass
    def getExpectations(self):
        # General function to get all relevant moments
        pass
    def updateParameters(self):
        # General function to update parameters of the Q distribution
        pass
    def update(self):
        # General function to update both parameters and expectations
        self.updateParameters()
        self.updateExpectations()
    def getParameters(self):
        # General function to get the parameters of the distributions
        pass

###################################################################
## General classes for observed and unobserved variational nodes ##
###################################################################

class Observed_Variational_Node(Variational_Node):
    """
    Abstract class for an observed variational node in a Bayesian probabilistic model.
    Observed variational nodes only contain a single distribution Q(X) which will be stored as
    instances of Distribution() as a .Q attribute.
    """
    def __init__(self, dim, obs):
        Variational_Node.__init__(self, dim)
        self.obs = obs
    def getObservations(self):
        return self.obs
    def getExpectation(self):
        return self.getObservations()
    # def getExpectations(self):
        # return { "obs":self.getObservations() }

class Unobserved_Variational_Node(Variational_Node):
    """
    Abstract class for an unobserved variational node in a Bayesian probabilistic model.
    Unobserved variational nodes contain a prior P(X) and a variational Q(X) distribution,
    which will be stored as instances of Distribution() attributes .P and .Q, respectively.
    The distributions are in turn composed of parameters and expectations
    """
    def __init__(self, dim):
        Variational_Node.__init__(self, dim)
        self.P = None
        self.Q = None
    def updateExpectations(self):
        self.Q.updateExpectations()

    def getExpectation(self):
        return self.Q.E

#######################################################
## Specific classes for unobserved variational nodes ##
#######################################################

class UnivariateGaussian_Unobserved_Variational_Node(Unobserved_Variational_Node):
    """
    Abstract class for a variational node where P(x) and Q(x)
    are both univariate Gaussian distributions.

    To save memory, we follow common practice and the the prior distribution is
    assumed to be the same for all elements
    """
    def __init__(self, dim, pmean, pvar, qmean, qvar, qE=None, qE2=None):
	    # dim (2d tuple): dimensionality of the node
	    # pmean (nd array): the mean parameter of the P distribution
	    # qmean (nd array): the mean parameter of the Q distribution
	    # pvar (nd array): the variance parameter of the P distribution
	    # qvar (nd array): the variance parameter of the Q distribution
	    # qE (nd array): the initial first moment of the Q distribution
	    # qE2 (nd array): the initial second moment of the Q distribution
        Unobserved_Variational_Node.__init__(self, dim)

        # Initialise the P and Q distributions
        # MODIFIED: dimensions of self.P have to match those of Q to allow informative
        # prior
        self.P = UnivariateGaussian(dim=dim, mean=pmean, var=pvar)
        self.Q = UnivariateGaussian(dim=dim, mean=qmean, var=qvar, E=qE, E2=qE2)

    def getParameters(self):
        return { 'mean': self.Q.mean, 'var': self.Q.var }
    def getExpectations(self):
        # return dict({'E':self.Q.E, 'E2':self.Q.E2, 'lnE':None})
        return dict({'E':self.Q.E, 'E2':self.Q.E2 })
class MultivariateGaussian_Unobserved_Variational_Node(Unobserved_Variational_Node):
    """
    Abstract class for a variational node where P(x) and Q(x)
    are both multivariate Gaussian distributions.

    Currently the prior of this distribution is not used anywhere so it is ignored to save memory
    """
    def __init__(self, dim, qmean, qcov, qE=None, qE2=None):
        # dim (2d tuple): dimensionality of the node
        # qmean (nd array): the mean parameter of the Q distribution
        # qcov (nd array): the covariance parameter of the Q distribution
        # qE (nd array): the initial first moment of the Q distribution
        # qE2 (nd array): the initial second moment of the Q distribution
        Unobserved_Variational_Node.__init__(self, dim)

        # Initialise the P and Q distributions
        # self.P = MultivariateGaussian(dim=dim, mean=pmean, cov=pcov)
        self.Q = MultivariateGaussian(dim=dim, mean=qmean, cov=qcov, E=qE, E2=qE2)

	def getParameters(self):
		return { 'mean':self.Q.mean, 'cov':self.Q.cov }
    def getExpectations(self):
        # return { 'E':self.Q.E, 'E2':self.Q.E2, 'lnE':None }
        return { 'E':self.Q.E, 'E2':self.Q.E2 }
class Gamma_Unobserved_Variational_Node(Unobserved_Variational_Node):
    """
    Abstract class for a variational node where P(x) and Q(x) are both gamma distributions
    """
    def __init__(self, dim, pa, pb, qa, qb, qE=None):
	    # dim (2d tuple): dimensionality of the node
	    # pa (nd array): the 'a' parameter of the P distribution
	    # qa (nd array): the 'a' parameter of the Q distribution
	    # pa (nd array): the 'b' parameter of the P distribution
	    # pb (nd array): the 'b' parameter of the Q distribution
	    # qE (nd array): the initial expectation of the Q distribution
        Unobserved_Variational_Node.__init__(self,dim)

        # Initialise the distributions
        self.P = Gamma(dim=(1,), a=pa, b=pb)
        self.Q = Gamma(dim=dim, a=qa, b=qb, E=qE)

    def getParameters(self):
        return { 'a':self.Q.a, 'b':self.Q.b }
    def getExpectations(self):
        # return { 'E':self.Q.E, 'lnE':self.Q.lnE, 'E2':None }
        return { 'E':self.Q.E, 'lnE':self.Q.lnE }
class Bernoulli_Unobserved_Variational_Node(Unobserved_Variational_Node):
    """
    Abstract class for a variational node where P(x) and Q(x)
    are both bernoulli distributions.

    To save memory, we follow common practice and the the prior distribution is
    assumed to be the same for all elements
    """
    def __init__(self, dim, ptheta, qtheta, qE=None):
	    # dim (2d tuple): dimensionality of the node
	    # ptheta (nd array): the 'theta' parameter of the P distribution
	    # qtheta (nd array): the 'theta' parameter of the Q distribution
	    # qE (nd array): the current moment of the Q distribution
        Unobserved_Variational_Node.__init__(self,dim)

        # Initialise the distributions
        self.P = Bernoulli(dim=(1,), theta=ptheta)
        self.Q = Bernoulli(dim=dim, theta=qtheta, E=qE)

    def getParameters(self):
        return { 'theta':self.Q.theta }
    def getExpectation(self):
        return self.Q.E
    def getExpectations(self):
        # return { 'E':self.Q.E, 'E2':None, 'lnE':None }
        return { 'E':self.Q.E }
class BernoulliGaussian_Unobserved_Variational_Node(Unobserved_Variational_Node):
    """
    Abstract class for a variational node where P(x) and Q(x)
    are joint gaussian-bernoulli distributions (see paper  Spike and Slab Variational Inference for
    Multi-Task and Multiple Kernel Learning by Titsias and Gredilla)

    This distribution has several expectations that are required for the variational updates, and they depend
    on other parameters (alpha from the ARD prior). For this reason I decided to define the expectations in the
    class of the corresponding node, instead of doing it here.

    The only element from the prior distribution that is used is S_ptheta, for this reason I ignore the other elements
    """
    def __init__(self, dim, qmean, qvar, ptheta, qtheta):
	    # dim (2d tuple): dimensionality of the node
	    # qmean (nd array): the mean parameter of the Q distribution
	    # qvar (nd array): the var parameter of the Q distribution
	    # ptheta (nd array): the theta parameter of the P distribution
	    # qtheta (nd array): the theta parameter of the Q distribution
        Unobserved_Variational_Node.__init__(self,dim)

        # Initialise the distributions
        # self.P = BernoulliGaussian(dim=(1,), theta=S_ptheta, mean=W_pmean, var=W_pvar)
        # initialise ptheta
        if type(ptheta) == float or len(ptheta) == 1:
            self.P_theta = ptheta * s.ones(dim[1])
        else:
            assert len(ptheta) == dim[1], "ptheta dimension mismatch"
            self.P_theta = ptheta

        self.Q = BernoulliGaussian(dim=dim, theta=qtheta, mean=qmean, var=qvar)

    def getParameters(self):
        return { 'theta':self.Q.theta, 'mean':self.Q.mean, 'var':self.Q.var }
    def getExpectation(self):
        return self.Q.ESW
