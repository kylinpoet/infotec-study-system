<template>
  <el-card class="panel-card chart-card" shadow="hover">
    <template #header>
      <div class="panel-head">
        <div>
          <h3>{{ panel.title }}</h3>
          <p class="panel-note chart-card__note">{{ panel.subtitle }}</p>
        </div>
        <el-tag effect="plain" round>{{ panel.unit ?? "指标" }}</el-tag>
      </div>
    </template>
    <VChart class="chart-view" :option="option" autoresize />
  </el-card>
</template>

<script setup lang="ts">
import { computed } from "vue";
import "../charts/setup";
import VChart from "vue-echarts";

import type { ChartPanel } from "../types/contracts";

const props = defineProps<{
  panel: ChartPanel;
}>();

const option = computed(() => {
  if (props.panel.chart_type === "pie") {
    return {
      color: ["#2F6FED", "#14B8A6", "#F59E0B", "#38BDF8"],
      tooltip: { trigger: "item" },
      legend: { bottom: 0, icon: "circle" },
      series: [
        {
          type: "pie",
          radius: ["42%", "72%"],
          center: ["50%", "44%"],
          label: { formatter: "{b}\n{d}%" },
          data: props.panel.points.map((point) => ({ name: point.label, value: point.value }))
        }
      ]
    };
  }

  return {
    color: ["#2F6FED"],
    tooltip: { trigger: "axis" },
    grid: { left: 24, right: 16, top: 16, bottom: 28, containLabel: true },
    xAxis: {
      type: "category",
      axisTick: { show: false },
      axisLine: { lineStyle: { color: "#D6DEE9" } },
      axisLabel: { color: "#52606D" },
      data: props.panel.points.map((point) => point.label)
    },
    yAxis: {
      type: "value",
      splitLine: { lineStyle: { color: "rgba(214, 222, 233, 0.65)" } },
      axisLabel: { color: "#52606D" }
    },
    series: [
      {
        type: props.panel.chart_type,
        smooth: props.panel.chart_type === "line",
        symbolSize: props.panel.chart_type === "line" ? 8 : 0,
        barWidth: props.panel.chart_type === "bar" ? 28 : undefined,
        areaStyle: props.panel.chart_type === "line" ? { color: "rgba(47, 111, 237, 0.12)" } : undefined,
        itemStyle: {
          borderRadius: props.panel.chart_type === "bar" ? [10, 10, 0, 0] : 0
        },
        data: props.panel.points.map((point) => point.value)
      }
    ]
  };
});
</script>
