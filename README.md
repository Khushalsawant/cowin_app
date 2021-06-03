# cowin_app
Cowin App is developed on PyQt5 as GUI based module.

This App is extracting current User location from browser by using python selenium & Chrome-driver. For live User location, It's extracted from integrating Application selenium Chrome driver,which gives output as User's latitude longitude.

Using geopy package, Current City/State/District is extracted by passing the input as User's latitude longitude. Connect to Cowin-Public API and extract the extract the vaccination slot on the basis of State & Districts. Filter those Vaccination slots on the basis of Current user location.

Based on current user location, it'll populate the vaccination session slot in table widget. User need to select the date for which he/She need to get the vaccination slot details in User area (including near by Postal code of 30-km radius). If User miss to select the date then App will generate the data based T+1 date as session date.
