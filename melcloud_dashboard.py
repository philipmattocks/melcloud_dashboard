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
#
# df = pd.read_csv('https://raw.githubusercontent.com/plotly/datasets/master/gapminderDataFiveYear.csv')
# df = pd.read_csv('./CSVReport_7Dec_short.csv')

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
df["date/time"] = pd.to_datetime(df["TimeStamp"], format='%d/%m/%Y %H:%M')
df["year"] = df["date/time"].dt.year
df = df[
    [
        "date/time",
        "year",
        "RoomTemperatureZone1",
        "RoomTemperatureZone2",
        "OutsideTemperature",
        "FlowTemperature",
        "EnergyConsumed",
        "EnergyProduced",
    ]
]
df_melted = df.melt(id_vars=["date/time", "year"], var_name="measurement", value_name="temp/energy")

app = Dash(__name__)
app.layout = html.Div(
    [
        dcc.DatePickerRange(
            id="my-date-picker-range",
            min_date_allowed=min(df["date/time"]),
            max_date_allowed=max(df["date/time"]),
            end_date=datetime.now().date() + timedelta(days=1),
            start_date=datetime.now().date() - timedelta(days=1)
            # initial_visible_month=date(2017, 8, 5),
            # start_date=min(df['date/time']),
            # end_date=max(df['date/time'])
        ),
        dcc.Graph(id="graph"),
        html.H3(id="output-container-date-picker-range"),
        html.H3(id="output-energy"),
        html.H3(id="total-consumed"),
        html.H3(id="total-produced"),
    ]
)


@app.callback(
    Output("output-container-date-picker-range", "children"),
    Output("output-energy", "children"),
    Output("total-consumed", "children"),
    Output("total-produced", "children"),
    Output("graph", "figure"),
    Input("my-date-picker-range", "start_date"),
    Input("my-date-picker-range", "end_date"),
)
def update_output(start_date, end_date):
    mask = (df_melted["date/time"] > datetime.strptime(start_date, '%Y-%m-%d')) & (df_melted["date/time"] <= datetime.strptime(end_date,'%Y-%m-%d'))
    filtered_df = df_melted.loc[mask]
    fig = px.line(filtered_df, x="date/time", y="temp/energy", color="measurement")
    fig.update_layout(transition_duration=500)
    mean_outside_temp = round(
        filtered_df.loc[filtered_df["measurement"] == "OutsideTemperature"][
            "temp/energy"
        ].mean(),
        2,
    )
    total_energy_produced = filtered_df.loc[
        filtered_df["measurement"] == "EnergyProduced"
    ]["temp/energy"].sum()
    total_energy_consumed = filtered_df.loc[
        filtered_df["measurement"] == "EnergyConsumed"
    ]["temp/energy"].sum()
    return (
        f"mean outside temp: {mean_outside_temp}",
        f"kWh Produced: {total_energy_produced/1000}",
        f"kWh Consumed: {total_energy_consumed/1000}",
        f"COP: {round(total_energy_produced / total_energy_consumed, 2)}",
        fig,
    )


if __name__ == "__main__":
    app.run_server(debug=False)
