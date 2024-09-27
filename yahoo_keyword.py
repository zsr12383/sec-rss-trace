import logging

logger = logging.getLogger(__name__)

spare_data = {'Federal investment',
              'FDA approval',
              'Federal funding',
              'demonstrated',
              'breakthrough',
              'clinical trial',
              'Earnings beat',
              'Revenue growth',
              'Record profits',
              'Profit increase',
              'Strong earnings',
              'earning surprise',
              'Earnings increase',
              'Received funding',
              'Selected for a grant',
              'Funding approved ',
              'Approved for funding',
              'Government grant',
              'Successful trial',
              'Well tolerated',
              'Met primary endpoint',
              'Met primary endpoints',
              'Achieved desired effect',
              'Clinical benefit',
              'Record revenue',
              'Major deal',
              'Record profits'
              'Drug approval',
              'Oil discovery',
              'Profit surge'
              }

magnificent = {
    'apple',
    'microsoft',
    'alphabet',
    'google',
    'amazon',
    'tesla',
    'nvidia',
    'meta'
}


def get_yahoo_keywords():
    return spare_data


def get_magnificent():
    return magnificent
