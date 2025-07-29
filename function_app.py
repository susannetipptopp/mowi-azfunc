import logging
import json
import datetime

import azure.functions as func
import pandas as pd

from mowi_finance import (
    get_mowi_data,
    get_mowi_history,
    get_mowi_actions,
    get_mowi_financials,
    get_mowi_recommendations,
)

def df_to_records(df: pd.DataFrame) -> list[dict]:
    """
    Reset index, convert any Timestamp or datetime column names to ISO strings,
    then return to_dict(orient='records').
    """
    df = df.reset_index()

    # Rename columns: any datetime-like → ISO string, others → str()
    new_cols = {}
    for col in df.columns:
        if isinstance(col, (pd.Timestamp, datetime.datetime, datetime.date)):
            new_cols[col] = col.isoformat()
        else:
            new_cols[col] = str(col)
    df = df.rename(columns=new_cols)

    return df.to_dict(orient="records")


class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


app = func.FunctionApp()

# ===== GetMowiData (full payload) =====
@app.function_name(name="GetMowiData")
@app.route(route="GetMowiData", auth_level=func.AuthLevel.ANONYMOUS)
def GetMowiData(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("GetMowiData HTTP trigger processed a request.")

    # Parse optional 'days' param (default 30)
    days_param = req.params.get("days")
    try:
        days = int(days_param) if days_param else 30
    except ValueError:
        days = 30

    try:
        # Fetch all data
        quote = get_mowi_data()
        history_df = get_mowi_history(days)
        actions_df = get_mowi_actions()
        financials = get_mowi_financials()
        recs_df = get_mowi_recommendations()

        # Build the payload, converting each DataFrame via df_to_records
        payload = {
            "quote": quote,
            "history": df_to_records(history_df),
            "actions": df_to_records(actions_df),
            "financials": {
                stmt: df_to_records(df)
                for stmt, df in financials.items()
            },
            "recommendations": df_to_records(recs_df),
        }

        # Serialize to JSON, with full ISO dates for any datetime values
        body = json.dumps(payload, cls=DateTimeEncoder)

        return func.HttpResponse(
            body=body,
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        logging.error("Error fetching Mowi data", exc_info=True)
        error_body = json.dumps({"error": str(e)})
        return func.HttpResponse(
            body=error_body,
            status_code=500,
            mimetype="application/json"
        )
