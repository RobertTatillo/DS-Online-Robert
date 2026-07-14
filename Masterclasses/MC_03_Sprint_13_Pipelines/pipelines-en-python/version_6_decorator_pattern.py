import pandas as pd
import uuid
from utils.xml_adapter import XMLAdpater
import time

def logging_decorator(func):
    def inner(*args, **kwargs):
        t1 = time.time()
        time.sleep(5)
        print(f"Llamando funcion: {func.__name__}")
        result = func(*args, **kwargs)
        t2 = time.time()
        print(f"Función completada")
        print(f"Tiempo de ejecución: {t2 - t1}")
        return result
    return inner

@logging_decorator
def pipeline(*steps):
    def wrapper(inputs):
        for step in steps:
            inputs = apply(step, inputs)
        return inputs
    return wrapper

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

df1 = XMLAdpater("data/xml/shopping_behavior_2023.xml").get_data()
df2 = XMLAdpater("data/xml/shopping_behavior_2024.xml").get_data()
df3 = XMLAdpater("data/xml/shopping_behavior_2025.xml").get_data()

p = pipeline(step1, step2, step3, step4)
p([df1, df2, df3])