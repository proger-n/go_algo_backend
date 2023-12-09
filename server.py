from fastapi import FastAPI
from pydantic import BaseModel
import json
import uvicorn
from fastapi.middleware.cors import CORSMiddleware
import pandas as pd
from datetime import datetime, timedelta

app = FastAPI()

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class InputData(BaseModel):
    money_input: int
    company_input: list
    period_input: str
    strategy: str


# df = pd.read_csv(
#     "https://drive.google.com/uc?export=download&confirm=no_antivirus&id=1koIRbvB8ChIoxupO2dsEnA52Z9p121YU")
df = pd.read_csv(
    "https://drive.google.com/uc?export=download&confirm=no_antivirus&id=10BQGAmRvfrHTSjyvyFNYemsn8FseTNSF")


def week(df, company):
    df["Date"] = pd.to_datetime(df["Date"])
    df_return = df[(df.Date > (datetime.now() - timedelta(days=7)))
              & (df.Date < (datetime.now() + timedelta(days=7)))
              & (df.Stock.isin(company))]
    df_return["Date"] = df_return["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df_return


def action(df, company, input_money):
    df_result = pd.DataFrame()
    for comp in company:
        df_result = df_result.append(df[(df.Stock == comp) & (
            df.signal_rol == 1)].head(1), ignore_index=True)
    # df_result["Date"] = df_result["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")
    # df_coef = df.groupby(["Stock"], as_index=False).agg({"Predicted_Close": "first"}) # Заменить на коэф для компании
    for comp in company:
        df_result = df_result.append(df[(df.Stock == comp) & (df.signal_rol == -1)].head(1), ignore_index= True)
    df_result["Date"] = df_result["Date"].dt.strftime("%Y-%m-%d %H:%M:%S")

    df_result["amount"] = 0
    flag = 1
    while flag:
        flag = 0
        for i in range(len(df_result)//2):
            if df_result.iloc[i, 3] < input_money:
                df_result.iloc[i, 5] += 1
                input_money -= df_result.iloc[i, 3]
                flag = 1

    for i in range(len(df_result)//2):
        df_result.iloc[len(df_result)//2+i, 5] = df_result.iloc[i,5]
    df_sell = df_result.iloc[len(df_result)//2 : ].copy()
    df_buy = df_result.iloc[0 : len(df_result)//2]
    flag = 1
    while flag:
        flag = 0
        for i in range(len(df_result)//2, len(df_result)):
            if df_result.iloc[i, 5] > 0:
                df_result.iloc[i, 5] -= 1
                input_money += df_result.iloc[i, 3]
                flag = 1

    return df_buy, df_sell, input_money


def parse_csv(df):
    res = df.to_json(orient="records")
    parsed = json.loads(res)
    return parsed



@app.post('/select')
def select(inp: InputData):
    """
    :param input: input data from the post request
    :return: predicted cost of stock by date
    """
    money = inp.money_input
    df_week = week(df, inp.company_input)
    df_buy, df_sell, money = action(df, inp.company_input, money)
    return {
        "money": money,
        "date_cost": parse_csv(df_week),
        "buy" : parse_csv(df_buy),
        "sell" : parse_csv(df_sell),
        "percent" : (money/inp.money_input - 1) * 100,
        "date_exit" : parse_csv(df_sell.tail(1).Date)
    }