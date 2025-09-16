import os

class Config:
    DEBUG = False
    DEVELOPMENT = False
    
class ProductionConfig(Config):
    pass

class DevelopmentConfig(Config):
    DEBUG = True
    DEVELOPMENT = True

class TestingConfig(Config):
    DEBUG = True
    DEVELOPMENT = True
    TESTING = True