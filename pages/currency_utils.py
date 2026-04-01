import streamlit as st

def convert_price(val, target):
    rates = {"SEK": 11.5, "USD": 1.08, "EUR": 1.0}
        return val * rates.get(target, 1.0)
        