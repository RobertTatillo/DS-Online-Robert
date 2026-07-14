import pandas as pd

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
    with open("result.txt", "w") as f:
        for customer_id, category in result:
            f.write(f"{customer_id}, {category}\n")


df = pd.read_csv("data/csv/shopping_behavior_2023.csv")
step4(step3(step2(step1(df))))