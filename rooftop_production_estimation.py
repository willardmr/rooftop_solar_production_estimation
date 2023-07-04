import pandas as pd

NREL_API_KEY = "YOUR API KEY HERE"

LAS_VEGAS_LATTITUDE = 36.17
LAS_VEGAS_LONGITUDE = 115.139
PVWATTS_API_URL = "https://developer.nrel.gov/api/pvwatts/v8.json?api_key={api}&losses=14&azimuth=180&system_capacity={capacity}&array_type=1&module_type=0&tilt={tilt}&lat={lat}&lon={lon}&timeframe=hourly"
ENERGY_PRODUCTION_DATA = "Solar_Energy_Production_Sites.csv"
AVERAGE_PANEL_KW = 0.25


class Estimator:
    def output():
        production = pd.read_csv(
            ENERGY_PRODUCTION_DATA, thousands=',')
        panels_per_facility = production[production["Facility"].str.contains("Fire Station")][["Facility",
                                                                                               "Number_of_Panels"]].drop_duplicates()
        monthly_error = []
        yearly_error = []

        for _index, data in panels_per_facility.iterrows():
            url = PVWATTS_API_URL.format(
                api=NREL_API_KEY, capacity=data["Number_of_Panels"] *
                AVERAGE_PANEL_KW,
                lat=LAS_VEGAS_LATTITUDE, lon=LAS_VEGAS_LONGITUDE, tilt=10)

            simulated_monthly_production = pd.read_json(url, lines=True)
            actual_monthly_production = production[(production["Facility"] == data["Facility"]) & (~production["KWH_Generated"].isna()) & (
                production["Date"].str.contains("2020"))][["KWH_Generated"]]
            if actual_monthly_production.shape[0] < 12:
                print("Not enough rows")
                continue

            thing = pd.DataFrame(simulated_monthly_production.head()[
                'outputs'][0]['ac_monthly'], columns=['production']).reset_index()
            simulated_and_actual_productions = pd.merge(
                thing, actual_monthly_production.reset_index(), left_index=True, right_index=True)

            error = (abs(simulated_and_actual_productions['KWH_Generated'] -
                     simulated_and_actual_productions['production']))/simulated_and_actual_productions['KWH_Generated']
            monthly_error += error.values.tolist()

            yearly_error.append((abs(sum(simulated_and_actual_productions['KWH_Generated']) -
                                 sum(simulated_and_actual_productions['production'])))/sum(simulated_and_actual_productions['KWH_Generated']))

        print("Average monthly error: ", sum(monthly_error)/len(monthly_error))
        print("Average yearly error: ", sum(yearly_error)/len(yearly_error))
        print("P95 monthly error: ", pd.DataFrame(monthly_error).quantile(0.95))
        print("P95 yearly error: ", pd.DataFrame(yearly_error).quantile(0.95))


if __name__ == "__main__":
    estimator = Estimator()
    Estimator.output()
