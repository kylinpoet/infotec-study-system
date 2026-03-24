<template>
  <el-card class="panel-card chart-card" shadow="hover">
    <template #header>
      <div class="chart-card__header">
        <div>
          <p class="panel-kicker">数据视图</p>
          <h3>{{ panel.title }}</h3>
          <p class="panel-note chart-card__note">{{ panel.subtitle }}</p>
        </div>
        <div class="chart-card__unit">{{ panel.unit ?? "指标" }}</div>
      </div>
    </template>
    <VChart class="chart-view" :option="option" autoresize />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { graphic } from "echarts/core";

import "../charts/setup";
import VChart from "vue-echarts";

import type { ChartPanel } from "../types/contracts";

const props = defineProps<{
  panel: ChartPanel;
}>();

const palette = ["#2563EB", "#10B981", "#F59E0B", "#F97316", "#8B5CF6"];

const pieTotal = computed(() =>
  props.panel.points.reduce((total, point) => total + point.value, 0)
);

const option = computed(() => {
  if (props.panel.chart_type === "pie") {
    return {
      color: palette,
      tooltip: {
        trigger: "item",
        backgroundColor: "rgba(15, 23, 42, 0.92)",
        borderWidth: 0,
        textStyle: { color: "#F8FAFC" },
      },
      series: [
        {
          type: "pie",
          radius: ["52%", "76%"],
          center: ["50%", "46%"],
          avoidLabelOverlap: true,
          label: {
            color: "#475569",
            formatter: "{b}\n{d}%",
          },
          labelLine: {
            lineStyle: { color: "rgba(100, 116, 139, 0.4)" },
          },
          itemStyle: {
            borderColor: "rgba(255,255,255,0.98)",
            borderWidth: 3,
            shadowBlur: 16,
            shadowColor: "rgba(37, 99, 235, 0.12)",
          },
          data: props.panel.points.map((point, index) => ({
            name: point.label,
            value: point.value,
            itemStyle: {
              color: palette[index % palette.length],
            },
          })),
        },
      ],
      graphic: [
        {
          type: "group",
          left: "center",
          top: "36%",
          children: [
            {
              type: "text",
              style: {
                text: String(pieTotal.value),
                fontSize: 24,
                fontWeight: 700,
                fill: "#0F172A",
                textAlign: "center",
              },
            },
            {
              type: "text",
              top: 28,
              style: {
                text: props.panel.unit ?? "总量",
                fontSize: 12,
                fill: "#64748B",
                textAlign: "center",
              },
            },
          ],
        },
      ],
    };
  }

  const seriesColor =
    props.panel.chart_type === "line"
      ? "#0EA5E9"
      : new graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: "#2563EB" },
          { offset: 1, color: "#60A5FA" },
        ]);

  return {
    animationDuration: 700,
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: props.panel.chart_type === "bar" ? "shadow" : "line",
        shadowStyle: { color: "rgba(37, 99, 235, 0.06)" },
        lineStyle: { color: "rgba(37, 99, 235, 0.25)" },
      },
      backgroundColor: "rgba(15, 23, 42, 0.92)",
      borderWidth: 0,
      textStyle: { color: "#F8FAFC" },
    },
    grid: { left: 16, right: 12, top: 18, bottom: 24, containLabel: true },
    xAxis: {
      type: "category",
      boundaryGap: props.panel.chart_type === "bar",
      axisTick: { show: false },
      axisLine: { show: false },
      axisLabel: {
        color: "#64748B",
        fontSize: 12,
      },
      data: props.panel.points.map((point) => point.label),
    },
    yAxis: {
      type: "value",
      axisLine: { show: false },
      axisTick: { show: false },
      axisLabel: {
        color: "#94A3B8",
        fontSize: 12,
      },
      splitLine: {
        lineStyle: {
          color: "rgba(148, 163, 184, 0.16)",
          type: "dashed",
        },
      },
    },
    series: [
      {
        type: props.panel.chart_type,
        smooth: props.panel.chart_type === "line",
        symbol: props.panel.chart_type === "line" ? "circle" : "none",
        symbolSize: props.panel.chart_type === "line" ? 8 : 0,
        barWidth: props.panel.chart_type === "bar" ? 26 : undefined,
        itemStyle: {
          color: seriesColor,
          borderRadius: props.panel.chart_type === "bar" ? [12, 12, 4, 4] : 0,
          shadowBlur: props.panel.chart_type === "bar" ? 16 : 0,
          shadowColor: "rgba(37, 99, 235, 0.16)",
        },
        lineStyle: {
          width: 3,
          color: "#0EA5E9",
        },
        areaStyle:
          props.panel.chart_type === "line"
            ? {
                color: new graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: "rgba(14, 165, 233, 0.28)" },
                  { offset: 1, color: "rgba(14, 165, 233, 0.02)" },
                ]),
              }
            : undefined,
        emphasis: {
          scale: props.panel.chart_type === "bar",
        },
        data: props.panel.points.map((point) => point.value),
      },
    ],
  };
});
</script>
