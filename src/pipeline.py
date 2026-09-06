import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SRC_DIR.parent

def load_data(filepath):
    df = pd.read_csv(filepath)
    print(f"[load]  {filepath} -> {len(df)} baris")
    return df

def clean_data(df):
    before = len(df)

    df = df.dropna(subset=["transaction_date"])

    df[["make", "num-of-doors"]] = df[["make", "num-of-doors"]].fillna("unknown")

    df["horsepower-binned"] = df["horsepower-binned"].fillna(
        pd.cut(
            df["horsepower"],
            bins=[-float("inf"), 101, 155, float("inf")],
            labels=["Low", "Medium", "High"]
        )
    )

    df["stroke"] = df["stroke"].fillna(df["stroke"].mean())
    df["price"] = df["price"].fillna(df["price"].median())
    df["horsepower"] = df["horsepower"].fillna(
        df.groupby("horsepower-binned", observed=True)["horsepower"]
        .transform("median")

    )
    df = df.drop_duplicates()

    df["transaction_date"] = pd.to_datetime(
        df["transaction_date"], errors="coerce", format="mixed"
    )

    cols = ["make", "body-style", "drive-wheels", "fuel-system"]
    df[cols] = df[cols].apply(lambda col: col.str.lower().str.strip())

    print(f"[clean] {before} -> {len(df)} baris ({before - len(df)} dibuang)")
    return df

def transform_data(df):
    mapping = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "unknown": -1
    }
    cols = ["num-of-doors", "num-of-cylinders"]
    df[cols] = df[cols].replace(mapping)

    scaler = MinMaxScaler()
    cols_to_normalize = [
        "normalized-losses",
        "wheel-base",
        "length",
        "width",
        "height",
        "curb-weight",
        "engine-size",
        "bore",
        "stroke",
        "compression-ratio",
        "horsepower",
        "peak-rpm",
        "city-mpg",
        "highway-mpg",
        "price",
        "city-L/100km"
    ]
    df[cols_to_normalize] = scaler.fit_transform(df[cols_to_normalize])

    categorical_cols = [
        "make",
        "aspiration",
        "body-style",
        "drive-wheels",
        "engine-location",
        "engine-type",
        "fuel-system",
        "horsepower-binned"
    ]
    df = pd.get_dummies(df, columns=categorical_cols, dtype=int)
    return df

def save_data(df, filepath):
    df.to_csv(filepath, index=False)

def main():
    print("Mulai jalankan pipeline...")
    df = load_data(f"{PROJECT_DIR}/data/raw/automobileEDA_dirty_training.csv")
    df = clean_data(df)
    df = transform_data(df)
    save_data(df, f"{PROJECT_DIR}/data/processed/automobileEDA_processed.csv")
    print("Pipeline selesai...")

if __name__ == "__main__":
    main()