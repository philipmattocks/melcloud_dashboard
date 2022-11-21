# melcloud_dashboard
Display data from a Mitsubishi Electric Heating system.  Data is downloaded from CSV MELcloud and displayed in locally hosted webpage.  The last 24 of data is selected initially but other date ranges can be selected by the user.

For this to work you need to set environmental variables with your MELCloud username and password:

`export MEL_USERNAME=<yourusername>`

`export MEL_PASSWORD=<yourpassword>`

Make sure the python requirments in `requirements.txt` are installed.

run with:

`python melcloud_dashboard`

and then navigate in browser to

`http://127.0.0.1:8050`
