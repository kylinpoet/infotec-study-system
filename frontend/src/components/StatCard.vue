<template>
  <el-card class="panel-card stat-card" shadow="never">
    <p class="panel-kicker">{{ title }}</p>
    <strong class="stat-card__value">{{ value }}</strong>
    <p class="panel-note">{{ hint }}</p>
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  value: string;
  hint: string;
}>();
</script>
