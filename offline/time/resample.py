import pandas as pd


def resample(file_in_path, file_out_path, rate="1H"):
    df = pd.read_csv(file_in_path, names=["time", "values"])
    ts = pd.Series(df["values"].values, index=pd.to_datetime(df["time"]))
    ts.resample(rate).mean().bfill().to_csv(file_out_path)








