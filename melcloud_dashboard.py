from datetime import date
from dash import Dash, dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import pandas as pd
import os
import requests
import json
from io import BytesIO
from datetime import timedelta
from datetime import datetime

# df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')
# df = pd.read_csv('./CSVReport_short.csv')

login_url = "https://app.melcloud.com/Mitsubishi.Wifi.Client/Login/ClientLogin"
username = os.environ.get("MEL_USERNAME")
password = os.environ.get("MEL_PASSWORD")

if username is None and password is None:
    raise ValueError(
        "Environmental variables MEL_USERNAME and MEL_PASSWORD not set, exiting.  Please set these and rerun.."
    )

login_dict = {
    "Email": username,
    "Password": password,
    "Language": 0,
    "AppVersion": "1.25.2.0",
    "Persist": True,
    "CaptchaResponse": None,
}
s = requests.Session()
print(f"Logging in to MelCoud...")
response_login = s.post(login_url, data=login_dict)

if json.loads(response_login.content.decode("utf8"))["ErrorId"]:
    raise ValueError(
        "Login to MELCloud unsuccessful, please check environmental variables MEL_USERNAME and"
        " MEL_PASSWORD are correctly set and rerun"
    )


key = json.loads(response_login.content.decode("utf8"))["LoginData"]["ContextKey"]
get_data_url = f"https://app.melcloud.com/Mitsubishi.Wifi.Client/Report/GetCSVReport?device=24725630&key={key}"
print(f"Getting data from MELCloud...")
response_get_data = s.get(get_data_url)
print(f"Processing data...")
df = pd.read_csv(BytesIO(response_get_data.content))
df["date"] = pd.to_datetime(df["TimeStamp"])
df["year"] = df["date"].dt.year
df = df[
    [
        "date",
        "year",
        "RoomTemperatureZone1",
        "RoomTemperatureZone2",
        "OutsideTemperature",
        "FlowTemperature",
        "EnergyConsumed",
        "EnergyProduced",
    ]
]
df_melted = df.melt(id_vars=["date", "year"], var_name="measurement", value_name="temp")

app = Dash(__name__)
app.layout = html.Div(
    [
        dcc.DatePickerRange(
            id="my-date-picker-range",
            min_date_allowed=min(df["date"]),
            max_date_allowed=max(df["date"]),
            end_date=datetime.now().date() + timedelta(days=1),
            start_date=datetime.now().date() - timedelta(days=1)
            # initial_visible_month=date(2017, 8, 5),
            # start_date=min(df['date']),
            # end_date=max(df['date'])
        ),
        dcc.Graph(id="graph"),
        html.H1(id="output-container-date-picker-range"),
        html.H1(id="output-energy"),
    ]
)


@app.callback(
    Output("output-container-date-picker-range", "children"),
    Output("output-energy", "children"),
    Output("graph", "figure"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date"),
)
def update_output(start_date, end_date):
    mask = (df_melted["date"] > start_date) & (df_melted["date"] <= end_date)
    filtered_df = df_melted.loc[mask]
    fig = px.line(filtered_df, x="date", y="temp", color="measurement")
    fig.update_layout(transition_duration=500)
    mean_outside_temp = round(
        filtered_df.loc[filtered_df["measurement"] == "OutsideTemperature"][
            "temp"
        ].mean(),
        2,
    )
    total_energy_produced = filtered_df.loc[
        filtered_df["measurement"] == "EnergyProduced"
    ]["temp"].sum()
    total_energy_consumed = filtered_df.loc[
        filtered_df["measurement"] == "EnergyConsumed"
    ]["temp"].sum()
    return (
        f"mean outside temp: {mean_outside_temp}",
        f"EnergyConsumed/EnergyProduced: {round(total_energy_produced/total_energy_consumed, 2)}",
        fig,
    )


if __name__ == "__main__":
    app.run_server(debug=False)
