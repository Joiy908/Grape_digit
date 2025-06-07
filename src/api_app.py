from datetime import datetime, timezone
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query
from influxdb_client import Point
from pydantic import AwareDatetime, BaseModel
from fastapi.middleware.cors import CORSMiddleware

from .influxdb import INFLUXDB_BUCKET, query_api, write_api
from .tools import TZ_UTC8, assert_timezone_aware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 传感器字段映射
SENSOR_FIELDS = {
    'v_temp_1': 'temperature',
    'v_humidity_1': 'humidity',
    'v_light_1': 'light_intensity',
    'v_soil_temp_1': 'soil_temperature',
    'v_wind_1': 'wind_speed',
    'v_soil_moisture_1': 'soil_moisture',
}


@app.get('/api/v1/sensors/values')
def get_all_sensor_values():
    flux_query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -1h)
      |> filter(fn: (r) => r._measurement == "env_data")
      |> filter(fn: (r) => r.sensor_id =~ /v_/ or r.sensor_id =~ /r_/)
      |> last()
      |> pivot(rowKey: ["_time"], columnKey: ["sensor_id", "_field"], valueColumn: "_value")
    """
    # print(flux_query)

    try:
        result = query_api.query(query=flux_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to query sensor data: {str(e)}')
    # print(result)
    data = []
    if result and len(result) > 0:
        row = result[0].records[0]
        row_time = row.get_time()
        assert_timezone_aware(row_time)
        row_time = row_time.astimezone(TZ_UTC8)

        for sensor_id, field in SENSOR_FIELDS.items():
            column_name = f'{sensor_id}_{field}'
            value = row.values.get(column_name)
            if value is not None:
                data.append({'sensor_id': sensor_id, 'field': field, 'value': value})

    if not data:
        return {'status': 'success', 'data': [], 'message': 'No recent data found'}

    return {'time': row_time, 'data': data}


# 请求模型
class IrrigationEvent(BaseModel):
    outlet: str
    vineyard_id: str
    amount: float
    area: float
    timestamp: AwareDatetime | None = None


class Event(BaseModel):
    vineyard_id: str
    event_type: str
    details: str | None = None
    timestamp: AwareDatetime | None = None



# 添加浇水事件
@app.post("/api/v1/irrigation_events")
def create_irrigation_event(event: IrrigationEvent):
    if event.timestamp is None:
        event.timestamp = datetime.now(tz=timezone.utc)

    print(event.timestamp)
    point = (
        Point("irrigation_events")
        .tag("outlet", event.outlet)
        .tag("vineyard_id", event.vineyard_id)
        .field("amount", event.amount)
        .field("area", event.area)
        .time(event.timestamp)
    )

    try:
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
    except Exception as e:
        raise HTTPException(status_code=499, detail=f"Failed to write irrigation event: {str(e)}")

    return {"status": "success"}

# 查询浇水事件
@app.get("/api/v1/irrigation_events")
def get_irrigation_events(
    start_time: AwareDatetime = Query(None),
    end_time: AwareDatetime = Query(None),
    outlet: str = Query(None),
    vineyard_id: str = Query(None),
    limit: int = Query(99, ge=1, le=1000)
):
    flux_query = f'from(bucket: "{INFLUXDB_BUCKET}")'
    if start_time and end_time:
        flux_query += f' |> range(start: {start_time.isoformat()}, stop:{end_time.isoformat()})'
    else:
        flux_query += ' |> range(start: -31d)'
    flux_query += ' |> filter(fn: (r) => r._measurement == "irrigation_events")'
    if outlet:
        flux_query += f' |> filter(fn: (r) => r.outlet == "{outlet}")'
    if vineyard_id:
        flux_query += f' |> filter(fn: (r) => r.vineyard_id == "{vineyard_id}")'
    flux_query += ' |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'
    flux_query += f'|> group() |> sort(columns: ["_time",], desc: true) |> limit(n: {limit})'

    # print(flux_query)
    try:
        result = query_api.query(query=flux_query)
    except Exception as e:
        # print(e)
        raise HTTPException(status_code=499, detail=f"Failed to query irrigation events: {str(e)}")

    data = []
    for table in result:
        for record in table.records:
            utc_time = record.get_time()
            shanghai_time = utc_time.astimezone(TZ_UTC8)
            data.append({
                "outlet": record.values["outlet"],
                "vineyard_id": record.values["vineyard_id"],
                "amount": record.values["amount"],
                "area": record.values["area"],
                "timestamp": shanghai_time.isoformat()
            })

    return {"status": "success", "data": data}

@app.post("/api/v1/events")
def create_event(event: Event):
    point = (
        Point("events")
        .tag("vineyard_id", event.vineyard_id)
        .tag("event_type", event.event_type)
        .field("details", event.details or "")
        .time(event.timestamp)
    )

    try:
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
    except Exception as e:
        raise HTTPException(status_code=499, detail=f"Failed to write event: {str(e)}")

    return {"status": "success"}

# 查询通用事件
@app.get("/api/v1/events")
def get_events(
    start_time: AwareDatetime = Query(None),
    end_time: AwareDatetime = Query(None),
    event_type: str = Query(None),
    vineyard_id: str = Query(None),
    limit: int = Query(99, ge=1, le=1000)
):
    flux_query = f'from(bucket: "{INFLUXDB_BUCKET}")'
    if start_time and end_time:
        flux_query += f' |> range(start: {start_time.isoformat()}, stop: {end_time.isoformat()})'
    else:
        flux_query += ' |> range(start: -31d)'
    flux_query += ' |> filter(fn: (r) => r._measurement == "events")'
    if event_type:
        flux_query += f' |> filter(fn: (r) => r.event_type == "{event_type}")'
    if vineyard_id:
        flux_query += f' |> filter(fn: (r) => r.vineyard_id == "{vineyard_id}")'
    flux_query += ' |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'
    flux_query += f' |> limit(n: {limit})'

    try:
        result = query_api.query(query=flux_query)
    except Exception as e:
        raise HTTPException(status_code=499, detail=f"Failed to query events: {str(e)}")

    data = []
    for table in result:
        for record in table.records:
            utc_time = record.get_time()
            shanghai_time = utc_time.astimezone(TZ_UTC8)
            data.append({
                "vineyard_id": record.values["vineyard_id"],
                "event_type": record.values["event_type"],
                "details": record.values["details"],
                "timestamp": shanghai_time.isoformat()
            })

    return {"status": "success", "data": data}


# 启动服务
if __name__ == '__main__':
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    res = get_all_sensor_values()
    print(res)
