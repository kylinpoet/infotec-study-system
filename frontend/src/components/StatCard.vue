<template>
  <el-card class="panel-card stat-card" shadow="never">
    <div class="stat-card__top">
      <p class="panel-kicker">{{ title }}</p>
      <div v-if="$slots.icon" class="stat-card__icon">
        <slot name="icon" />
      </div>
    </div>
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
