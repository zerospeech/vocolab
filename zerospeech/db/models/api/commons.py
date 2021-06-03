""" Common types used in multiple api requests """
from pydantic import BaseModel


class Message(BaseModel):
    """ Generic message response"""
    message: str
