import numpy as np
from sklearn.linear_model import LinearRegression

def forecast_next_3(values):
    if len(values) < 3:
        return []

    # X = month numbers, Y = actual values
    values = values[-6:]
    X = np.array(range(len(values))).reshape(-1, 1)
    Y = np.array(values)

    model = LinearRegression()
    model.fit(X, Y)

    # Next 3 months predict karo
    next_months = np.array(range(len(values), len(values) + 3)).reshape(-1, 1)
    predictions = model.predict(next_months)

    # Round to 1 decimal
    return [round(p, 1) for p in predictions]