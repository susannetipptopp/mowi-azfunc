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

# ===== GetMowiData (full payload) adding comment to check if it gets deployed=====
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
# ===== GetMowiQuote =====
@app.function_name(name="GetMowiQuote")
@app.route(route="GetMowiQuote", auth_level=func.AuthLevel.ANONYMOUS)
def GetMowiQuote(req: func.HttpRequest) -> func.HttpResponse:
    """Returns the current Mowi quote as JSON."""
    try:
        quote = get_mowi_data()
        body = json.dumps(quote, cls=DateTimeEncoder)
        return func.HttpResponse(body=body, status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error("Error in GetMowiQuote", exc_info=True)
        error_body = json.dumps({"error": str(e)})
        return func.HttpResponse(
            body=error_body,
            status_code=500,
            mimetype="application/json"
        )

# ===== GetMowiHistory =====
@app.function_name(name="GetMowiHistory")
@app.route(route="GetMowiHistory", auth_level=func.AuthLevel.ANONYMOUS)
def GetMowiHistory(req: func.HttpRequest) -> func.HttpResponse:
    """Returns historical data for Mowi over the specified number of days."""
    try:
        days = int(req.params.get("days", 30))
        records = df_to_records(get_mowi_history(days))
        body = json.dumps(records, cls=DateTimeEncoder)
        return func.HttpResponse(body=body, status_code=200, mimetype="application/json")
    except ValueError:
        logging.warning("Invalid 'days' parameter for GetMowiHistory", exc_info=True)
        error_body = json.dumps({"error": "Parameter 'days' must be an integer."})
        return func.HttpResponse(
            body=error_body,
            status_code=400,
            mimetype="application/json"
        )
    except Exception as e:
        logging.error("Error in GetMowiHistory", exc_info=True)
        error_body = json.dumps({"error": str(e)})
        return func.HttpResponse(
            body=error_body,
            status_code=500,
            mimetype="application/json"
        )

# ===== GetMowiActions =====
@app.function_name(name="GetMowiActions")
@app.route(route="GetMowiActions", auth_level=func.AuthLevel.ANONYMOUS)
def GetMowiActions(req: func.HttpRequest) -> func.HttpResponse:
    """Returns corporate actions for Mowi."""
    try:
        actions = df_to_records(get_mowi_actions())
        body = json.dumps(actions, cls=DateTimeEncoder)
        return func.HttpResponse(body=body, status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error("Error in GetMowiActions", exc_info=True)
        error_body = json.dumps({"error": str(e)})
        return func.HttpResponse(
            body=error_body,
            status_code=500,
            mimetype="application/json"
        )

# ===== GetMowiFinancials =====
@app.function_name(name="GetMowiFinancials")
@app.route(route="GetMowiFinancials", auth_level=func.AuthLevel.ANONYMOUS)
def GetMowiFinancials(req: func.HttpRequest) -> func.HttpResponse:
    """Returns the financial statements for Mowi."""
    try:
        financials = get_mowi_financials()
        formatted = {stmt: df_to_records(df) for stmt, df in financials.items()}
        body = json.dumps(formatted, cls=DateTimeEncoder)
        return func.HttpResponse(body=body, status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error("Error in GetMowiFinancials", exc_info=True)
        error_body = json.dumps({"error": str(e)})
        return func.HttpResponse(
            body=error_body,
            status_code=500,
            mimetype="application/json"
        )

# ===== GetMowiRecommendations =====
@app.function_name(name="GetMowiRecommendations")
@app.route(route="GetMowiRecommendations", auth_level=func.AuthLevel.ANONYMOUS)
def GetMowiRecommendations(req: func.HttpRequest) -> func.HttpResponse:
    """Returns analyst recommendations for Mowi."""
    try:
        recs = df_to_records(get_mowi_recommendations())
        body = json.dumps(recs, cls=DateTimeEncoder)
        return func.HttpResponse(body=body, status_code=200, mimetype="application/json")
    except Exception as e:
        logging.error("Error in GetMowiRecommendations", exc_info=True)
        error_body = json.dumps({"error": str(e)})
        return func.HttpResponse(
            body=error_body,
            status_code=500,
            mimetype="application/json"
        )

        

