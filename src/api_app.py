from datetime import timedelta
from typing import Annotated, Literal

from fastapi import FastAPI, HTTPException, Query
from influxdb_client import Point
from pydantic import AwareDatetime, BaseModel

from .influxdb import INFLUXDB_BUCKET, query_api, write_api

app = FastAPI()


# 传感器字段映射
SENSOR_FIELDS = {
    'v_temp_1': 'temperature',
    'v_humidity_1': 'humidity',
    'v_light_1': 'light_intensity',
    'v_soil_temp_1': 'soil_temperature',
    'v_wind_1': 'wind_speed',
    'v_soil_moisture_1': 'soil_moisture',
}


def to_shanghai_time(utc_time):
    return utc_time + timedelta(hours=8)


@app.get('/api/v1/sensors/values')
def get_all_sensor_values():
    flux_query = f"""
    from(bucket: "{INFLUXDB_BUCKET}")
      |> range(start: -35h)
      |> filter(fn: (r) => r._measurement == "env_data")
      |> filter(fn: (r) => r.sensor_id =~ /v_/ or r.sensor_id =~ /r_/)
      |> last()
      |> pivot(rowKey: ["_time"], columnKey: ["sensor_id", "_field"], valueColumn: "_value")
    """
    print(flux_query)

    try:
        result = query_api.query(query=flux_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to query sensor data: {str(e)}')
    print(result)
    data = []
    if result and len(result) > 0:
        row = result[0].records[0]
        shanghai_time = to_shanghai_time(row.get_time()).isoformat()
        print(row.values)

        for sensor_id, field in SENSOR_FIELDS.items():
            column_name = f'{sensor_id}_{field}'
            value = row.values.get(column_name)
            if value is not None:
                data.append({'sensor_id': sensor_id, 'field': field, 'value': value})

    if not data:
        return {'status': 'success', 'data': [], 'message': 'No recent data found'}

    return {'time': shanghai_time, 'data': data}


# 请求模型
class Record(BaseModel):
    type: Literal['irrigation', 'fertilizer']
    amount: float
    details: str | None = None
    timestamp: AwareDatetime


@app.post('/api/v1/records')
async def create_record(record: Record):
    point = (
        Point('irrigation_fertilizer_records')
        .tag('type', record.type)
        .field('amount', record.amount)
        .field('details', record.details or '')
        .time(record.timestamp)
    )

    try:
        write_api.write(bucket=INFLUXDB_BUCKET, record=point)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to write record: {str(e)}')

    return {'status': 'success'}


class GetRecordsParams(BaseModel):
    start_time: AwareDatetime
    end_time: AwareDatetime | None = None
    type: Literal['irrigation', 'fertilizer']


@app.get('/api/v1/records')
async def get_records(params: Annotated[GetRecordsParams, Query()]):
    flux_query = f'from(bucket: "{INFLUXDB_BUCKET}")'
    if params.end_time:
        flux_query += f' |> range(start: {params.start_time.isoformat()}, stop: {params.end_time.isoformat()})'
    else:
        flux_query += f' |> range(start: {params.start_time.isoformat()})'
    flux_query += ' |> filter(fn: (r) => r._measurement == "irrigation_fertilizer_records")'
    flux_query += f' |> filter(fn: (r) => r.type == "{params.type}")'
    flux_query += ' |> pivot(rowKey: ["_time"], columnKey: ["_field"], valueColumn: "_value")'

    try:
        result = query_api.query(query=flux_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'Failed to query records: {str(e)}')

    data = []
    for table in result:
        for record in table.records:
            data.append(
                {
                    'type': record.values['type'],
                    'amount': record.values['amount'],
                    'details': record.values['details'],
                    'timestamp': to_shanghai_time(record.get_time()),
                }
            )

    return {'status': 'success', 'data': data}


# 启动服务
if __name__ == '__main__':
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    res = get_all_sensor_values()
    print(res)
