import pandas as pd
import uuid

def step1(df):
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    df = df[df["payment_method"] == "PayPal"]
    df = df[df["frequency_of_purchases"].isin(["Weekly", "Fortnightly", "bi-weekly"])]
    return df

def step2(df):
    df = df[["customer_id", "category", "purchase_amount_(usd)"]].groupby(["customer_id", "category"]).sum().reset_index()
    df["rank"] = df.groupby("category")["purchase_amount_(usd)"].rank(method="dense", ascending=False)
    df = df[df["rank"] == 1]
    return df

def step3(df):
    values = df[["customer_id", "category"]].to_dict()
    customers = [x for x in values["customer_id"].values()]
    categories = [x for x in values["category"].values()]
    result = list(zip(customers, categories))

    return result

def step4(result):
    id = uuid.uuid4()
    with open(f"result_{id}.txt", "w") as f:
        for customer_id, category in result:
            f.write(f"{customer_id}, {category}\n")

def apply(step, values):
    return [step(value) for value in values]

df1 = pd.read_csv("data/csv/shopping_behavior_2023.csv")
df2 = pd.read_csv("data/csv/shopping_behavior_2024.csv")
df3 = pd.read_csv("data/csv/shopping_behavior_2025.csv")

apply(step4,
    apply(step3,
        apply(step2, 
            apply(step1, [df1, df2, df3]))))
