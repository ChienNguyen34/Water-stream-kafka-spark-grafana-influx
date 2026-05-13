docker exec spark-master /opt/spark/bin/spark-submit `
  --master spark://spark-master:7077 `
  --conf spark.jars.ivy=/tmp/.ivy2 `
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.8 `
  /opt/spark-apps/stream_processor.py

# 1. Xóa checkpoint cũ
docker exec -u root spark-master bash -c "rm -rf /tmp/spark-checkpoint/* && chmod 777 /tmp/spark-checkpoint"

{
  "title": "BATADAL Water Network",
  "uid": "batadal-water",
  "schemaVersion": 39,
  "refresh": "5s",
  "time": {
    "from": "now-10m",
    "to": "now"
  },
  "panels": [
    {
      "id": 1,
      "type": "canvas",
      "title": "Network Topology — CTOWN (Supply Chain)",
      "gridPos": {
        "h": 27,
        "w": 24,
        "x": 0,
        "y": 0
      },
      "datasource": {
        "type": "influxdb",
        "uid": "influxdb-water"
      },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: -2m)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) =>\n      r._field == \"L_T1\" or r._field == \"L_T2\" or r._field == \"L_T3\" or\n      r._field == \"L_T4\" or r._field == \"L_T5\" or r._field == \"L_T6\" or\n      r._field == \"L_T7\" or\n      r._field == \"S_PU1\" or r._field == \"S_PU2\" or r._field == \"S_PU3\" or\n      r._field == \"S_PU4\" or r._field == \"S_PU5\" or r._field == \"S_PU6\" or\n      r._field == \"S_PU7\" or r._field == \"S_PU8\" or r._field == \"S_PU9\" or\n      r._field == \"S_V2\" or\n      r._field == \"disp_PU1\" or r._field == \"disp_PU2\" or r._field == \"disp_PU3\"\n  )\n  |> last()\n  |> pivot(rowKey: [\"_time\"], columnKey: [\"_field\"], valueColumn: \"_value\")"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "thresholds": {
            "mode": "absolute",
            "steps": [
              {
                "color": "#6B7280",
                "value": 0
              },
              {
                "color": "green",
                "value": 1
              }
            ]
          }
        },
        "overrides": [
          {
            "matcher": {
              "id": "byRegexp",
              "options": "^disp_PU"
            },
            "properties": [
              {
                "id": "thresholds",
                "value": {
                  "mode": "absolute",
                  "steps": [
                    { "color": "#6B7280", "value": 0 },
                    { "color": "green",   "value": 1 },
                    { "color": "#DC2626", "value": 2 }
                  ]
                }
              }
            ]
          },
          {
            "matcher": {
              "id": "byRegexp",
              "options": "^L_T"
            },
            "properties": [
              {
                "id": "thresholds",
                "value": {
                  "mode": "absolute",
                  "steps": [
                    {
                      "color": "#DC2626",
                      "value": 0
                    },
                    {
                      "color": "#1D4ED8",
                      "value": 1
                    },
                    {
                      "color": "#3B82F6",
                      "value": 3
                    },
                    {
                      "color": "#DC2626",
                      "value": 6.3
                    }
                  ]
                }
              }
            ]
          }
        ]
      },
      "options": {
        "inlineEditing": true,
        "panZoom": false,
        "root": {
          "background": {
            "color": {
              "fixed": "#0F172A"
            }
          },
          "border": {
            "color": {
              "fixed": "transparent"
            }
          },
          "constraint": {
            "horizontal": "left",
            "vertical": "top"
          },
          "elements": [
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Nguồn"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-1",
              "placement": {
                "height": 50,
                "left": 0,
                "top": 20,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "fixed": "#334155"
                }
              },
              "border": {
                "color": {
                  "fixed": "#94A3B8"
                },
                "width": 2
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "#F1F5F9"
                },
                "fontSize": 14,
                "text": {
                  "fixed": "S1 — Nguồn"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": -1,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 420,
                    "y": 81
                  },
                  "target": {
                    "x": 0.6615384615384615,
                    "y": 0.6363636363636364
                  },
                  "targetName": "Pump PU1",
                  "targetOriginal": {
                    "x": 323,
                    "y": 165
                  }
                },
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 1,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 670,
                    "y": 81
                  },
                  "target": {
                    "x": -0.6923076923076923,
                    "y": 0.6363636363636364
                  },
                  "targetName": "Pump PU2",
                  "targetOriginal": {
                    "x": 775,
                    "y": 165
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Source S1",
              "placement": {
                "height": 87,
                "left": 410,
                "top": 20,
                "width": 270
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Bơm\nchính"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-2",
              "placement": {
                "height": 50,
                "left": 0,
                "top": 155,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "disp_PU1",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#CBD5E1"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "PU1"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0.7,
                    "y": -0.7
                  },
                  "sourceOriginal": {
                    "x": 325.5,
                    "y": 201.75
                  },
                  "target": {
                    "x": -0.9925925925925926,
                    "y": 0.9692307692307692
                  },
                  "targetName": "Tank T1",
                  "targetOriginal": {
                    "x": 421,
                    "y": 312
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Pump PU1",
              "placement": {
                "height": 55,
                "left": 215,
                "top": 155,
                "width": 130
              },
              "type": "ellipse"
            },
            {
              "background": {
                "color": {
                  "field": "disp_PU2",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#CBD5E1"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "PU2"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": -0.7,
                    "y": -0.7
                  },
                  "sourceOriginal": {
                    "x": 774.5,
                    "y": 201.75
                  },
                  "target": {
                    "x": 0.9925925925925926,
                    "y": 0.8769230769230769
                  },
                  "targetName": "Tank T1",
                  "targetOriginal": {
                    "x": 689,
                    "y": 315
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Pump PU2",
              "placement": {
                "height": 55,
                "left": 755,
                "top": 155,
                "width": 130
              },
              "type": "ellipse"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Bể T1"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-3",
              "placement": {
                "height": 60,
                "left": 0,
                "top": 295,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "L_T1",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 3
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 15,
                "text": {
                  "fixed": "T1 — Bể chính"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 1,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 690,
                    "y": 376
                  },
                  "target": {
                    "x": -0.9692307692307692,
                    "y": 0.8545454545454545
                  },
                  "targetName": "Valve V2",
                  "targetOriginal": {
                    "x": 757,
                    "y": 449
                  }
                },
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": -1,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 420,
                    "y": 378
                  },
                  "target": {
                    "x": 0,
                    "y": 0.9272727272727272
                  },
                  "targetName": "Pump PU3",
                  "targetOriginal": {
                    "x": 280,
                    "y": 457
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T1",
              "placement": {
                "height": 124,
                "left": 410,
                "top": 276,
                "width": 270
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Bơm /\nVan"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-4",
              "placement": {
                "height": 50,
                "left": 0,
                "top": 445,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "disp_PU3",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#CBD5E1"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "PU3"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 280,
                    "y": 500
                  },
                  "target": {
                    "x": -0.01,
                    "y": 0.9692307692307692
                  },
                  "targetName": "Tank T3",
                  "targetOriginal": {
                    "x": 279,
                    "y": 571
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Pump PU3",
              "placement": {
                "height": 55,
                "left": 215,
                "top": 455,
                "width": 130
              },
              "type": "ellipse"
            },
            {
              "background": {
                "color": {
                  "field": "S_V2",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#FCD34D"
                },
                "width": 2
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "V2"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 820,
                    "y": 500
                  },
                  "target": {
                    "x": 0.01,
                    "y": 0.9384615384615385
                  },
                  "targetName": "Tank T2",
                  "targetOriginal": {
                    "x": 861,
                    "y": 577
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Valve V2",
              "placement": {
                "height": 55,
                "left": 755,
                "top": 445,
                "width": 130
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Bể\nT2/T3"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-5",
              "placement": {
                "height": 60,
                "left": 0,
                "top": 578,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "L_T3",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 2
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 15,
                "text": {
                  "fixed": "T3"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 280,
                    "y": 635
                  },
                  "target": {
                    "x": 0.08333333333333333,
                    "y": 0.9636363636363636
                  },
                  "targetName": "Pump PU4",
                  "targetOriginal": {
                    "x": 210,
                    "y": 706
                  }
                },
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 280,
                    "y": 640
                  },
                  "target": {
                    "x": 0.1,
                    "y": 0.7818181818181819
                  },
                  "targetName": "Pump PU5",
                  "targetOriginal": {
                    "x": 391,
                    "y": 711
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T3",
              "placement": {
                "height": 65,
                "left": 180,
                "top": 575,
                "width": 200
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "field": "L_T2",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 2
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 15,
                "text": {
                  "fixed": "T2"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T2",
              "placement": {
                "height": 65,
                "left": 767,
                "top": 578,
                "width": 200
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Bơm"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-6",
              "placement": {
                "height": 50,
                "left": 0,
                "top": 708,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "S_PU4",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#CBD5E1"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "PU4"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 205,
                    "y": 760
                  },
                  "target": {
                    "x": -0.02666666666666667,
                    "y": 0.8461538461538461
                  },
                  "targetName": "Tank T4",
                  "targetOriginal": {
                    "x": 218,
                    "y": 840
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Pump PU4",
              "placement": {
                "height": 55,
                "left": 145,
                "top": 705,
                "width": 120
              },
              "type": "ellipse"
            },
            {
              "background": {
                "color": {
                  "field": "S_PU5",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#CBD5E1"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "PU5"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 385,
                    "y": 760
                  },
                  "target": {
                    "x": -0.05333333333333334,
                    "y": 0.9076923076923077
                  },
                  "targetName": "J256 node",
                  "targetOriginal": {
                    "x": 439,
                    "y": 838
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Pump PU5",
              "placement": {
                "height": 55,
                "left": 329,
                "top": 703,
                "width": 120
              },
              "type": "ellipse"
            },
            {
              "background": {
                "color": {
                  "field": "S_PU6",
                  "fixed": "#6B7280"
                }
              },
              "border": {
                "color": {
                  "fixed": "#CBD5E1"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "PU6"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 0,
                    "y": -1
                  },
                  "sourceOriginal": {
                    "x": 659,
                    "y": 758
                  },
                  "target": {
                    "x": 0.013333333333333334,
                    "y": 0.8769230769230769
                  },
                  "targetName": "J415 node",
                  "targetOriginal": {
                    "x": 681,
                    "y": 839
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Pump PU6",
              "placement": {
                "height": 55,
                "left": 599,
                "top": 703,
                "width": 120
              },
              "type": "ellipse"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "right",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Bể /\nNút áp"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-7",
              "placement": {
                "height": 60,
                "left": 0,
                "top": 835,
                "width": 100
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "L_T4",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 2
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 15,
                "text": {
                  "fixed": "T4"
                },
                "valign": "middle"
              },
              "connections": [
                {
                  "color": {
                    "fixed": "rgb(204, 204, 220)"
                  },
                  "path": "straight",
                  "size": {
                    "fixed": 2,
                    "max": 10,
                    "min": 1
                  },
                  "source": {
                    "x": 1,
                    "y": 1
                  },
                  "sourceOriginal": {
                    "x": 290,
                    "y": 830
                  },
                  "target": {
                    "x": -0.8666666666666667,
                    "y": -0.6363636363636364
                  },
                  "targetName": "Pump PU6",
                  "targetOriginal": {
                    "x": 607,
                    "y": 748
                  }
                }
              ],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T4",
              "placement": {
                "height": 65,
                "left": 140,
                "top": 830,
                "width": 150
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "#1E293B"
                }
              },
              "border": {
                "color": {
                  "fixed": "#475569"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "#94A3B8"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "J256\n◉ Áp"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "J256 node",
              "placement": {
                "height": 65,
                "left": 362,
                "top": 835,
                "width": 150
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "#1E293B"
                }
              },
              "border": {
                "color": {
                  "fixed": "#475569"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "#94A3B8"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "J415\n◉ Áp"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "J415 node",
              "placement": {
                "height": 65,
                "left": 599,
                "top": 835,
                "width": 150
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "border": {
                "color": {
                  "fixed": "transparent"
                }
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "#475569"
                },
                "fontSize": 11,
                "text": {
                  "fixed": "Distribution Zone (T5 · T6 · T7)"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "lbl-dist",
              "placement": {
                "height": 35,
                "left": 860,
                "top": 653,
                "width": 290
              },
              "type": "text"
            },
            {
              "background": {
                "color": {
                  "field": "L_T5",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "T5"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T5",
              "placement": {
                "height": 90,
                "left": 860,
                "top": 688,
                "width": 88
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "field": "L_T6",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "T6"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T6",
              "placement": {
                "height": 90,
                "left": 967,
                "top": 688,
                "width": 88
              },
              "type": "rectangle"
            },
            {
              "background": {
                "color": {
                  "field": "L_T7",
                  "fixed": "#1D4ED8"
                }
              },
              "border": {
                "color": {
                  "fixed": "#93C5FD"
                },
                "width": 1
              },
              "config": {
                "align": "center",
                "color": {
                  "fixed": "white"
                },
                "fontSize": 13,
                "text": {
                  "fixed": "T7"
                },
                "valign": "middle"
              },
              "connections": [],
              "constraint": {
                "horizontal": "left",
                "vertical": "top"
              },
              "name": "Tank T7",
              "placement": {
                "height": 90,
                "left": 1074,
                "top": 688,
                "width": 88
              },
              "type": "rectangle"
            }
          ],
          "name": "root",
          "placement": {
            "height": 900,
            "left": 0,
            "top": 0,
            "width": 1200
          },
          "type": "frame"
        },
        "tooltip": {
          "disableForOneClick": false,
          "mode": "single"
        }
      }
    },
    {
      "id": 4,
      "type": "timeseries",
      "title": "Bể T1 — Mực nước (L_T1)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 27 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T1\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T1\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 1.0 or r._value > 6.3)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 6.5,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 1.0,  "color": "green" },
              { "value": 6.3,  "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    },
    {
      "id": 5,
      "type": "timeseries",
      "title": "Bể T2 — Mực nước (L_T2)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 35 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T2\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T2\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 0.5 or r._value > 5.5)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 5.9,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 0.5,  "color": "green" },
              { "value": 5.5,  "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    },
    {
      "id": 6,
      "type": "timeseries",
      "title": "Bể T3 — Mực nước (L_T3)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 43 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T3\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T3\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 1.0 or r._value > 5.3)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 6.75,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 1.0,  "color": "green" },
              { "value": 5.3,  "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    },
    {
      "id": 7,
      "type": "timeseries",
      "title": "Bể T4 — Mực nước (L_T4)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 51 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T4\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T4\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 2.0 or r._value > 4.5)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 4.7,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 2.0,  "color": "green" },
              { "value": 4.5,  "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    },
    {
      "id": 8,
      "type": "timeseries",
      "title": "Bể T5 — Mực nước (L_T5)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 59 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T5\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T5\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 1.5 or r._value > 4.0)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 4.5,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 1.5,  "color": "green" },
              { "value": 4.0,  "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    },
    {
      "id": 9,
      "type": "timeseries",
      "title": "Bể T6 — Mực nước (L_T6)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 67 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T6\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T6\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 4.5)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 4.0,
          "max": 7,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 4.5,  "color": "green" },
              { "value": 5.7, "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    },
    {
      "id": 10,
      "type": "timeseries",
      "title": "Bể T7 — Mực nước (L_T7)",
      "gridPos": { "h": 8, "w": 24, "x": 0, "y": 75 },
      "datasource": { "type": "influxdb", "uid": "influxdb-water" },
      "targets": [
        {
          "refId": "A",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T7\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)"
        },
        {
          "refId": "B",
          "query": "from(bucket: \"water_bucket\")\n  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n  |> filter(fn: (r) => r._measurement == \"water_telemetry\")\n  |> filter(fn: (r) => r._field == \"L_T7\")\n  |> aggregateWindow(every: v.windowPeriod, fn: mean, createEmpty: false)\n  |> filter(fn: (r) => r._value < 1.0 or r._value > 4.8)\n  |> map(fn: (r) => ({ r with _field: \"violation\" }))"
        }
      ],
      "fieldConfig": {
        "defaults": {
          "min": 0,
          "max": 5.0,
          "color": { "mode": "thresholds" },
          "custom": {
            "axisLabel": "m",
            "thresholdsStyle": { "mode": "line+area" }
          },
          "thresholds": {
            "mode": "absolute",
            "steps": [
              { "value": null, "color": "red" },
              { "value": 1.0,  "color": "green" },
              { "value": 4.8,  "color": "red" }
            ]
          }
        },
        "overrides": [
          {
            "matcher": { "id": "byName", "options": "violation" },
            "properties": [
              { "id": "color", "value": { "mode": "fixed", "fixedColor": "red" } },
              { "id": "custom.lineWidth", "value": 0 },
              { "id": "custom.showPoints", "value": "always" },
              { "id": "custom.pointSize", "value": 10 },
              { "id": "custom.fillOpacity", "value": 0 },
              { "id": "custom.hideFrom", "value": { "legend": true, "tooltip": false, "viz": false } }
            ]
          }
        ]
      },
      "options": {
        "legend": { "displayMode": "list", "placement": "bottom" },
        "tooltip": { "mode": "single" }
      }
    }
  ]
}