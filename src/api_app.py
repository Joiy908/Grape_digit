from datetime import timedelta

from fastapi import FastAPI, HTTPException

from .influxdb import INFLUXDB_BUCKET, query_api

app = FastAPI()


# 传感器字段映射
SENSOR_FIELDS = {
    "v_temp_1": "temperature",
    "v_humidity_1": "humidity",
    "v_light_1": "light_intensity",
    "v_soil_temp_1": "soil_temperature",
    "v_wind_1": "wind_speed",
    "v_soil_moisture_1": "soil_moisture"
}


def to_shanghai_time(utc_time):
    return utc_time + timedelta(hours=8)


@app.get("/api/v1/sensors/values")
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
        raise HTTPException(status_code=500, detail=f"Failed to query sensor data: {str(e)}")
    print(result)
    data = []
    if result and len(result) > 0:
        row = result[0].records[0]
        shanghai_time = to_shanghai_time(row.get_time()).isoformat()
        print(row.values)

        for sensor_id, field in SENSOR_FIELDS.items():
            column_name = f"{sensor_id}_{field}"
            value = row.values.get(column_name)
            if value is not None:
                data.append({
                    "sensor_id": sensor_id,
                    "field": field,
                    "value": value
                })


    if not data:
        return {"status": "success", "data": [], "message": "No recent data found"}

    return {
        "time": shanghai_time,
        "data": data
    }


# 启动服务
if __name__ == "__main__":
    # import uvicorn
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    res = get_all_sensor_values()
    print(res)
