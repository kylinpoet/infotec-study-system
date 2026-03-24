<template>
  <el-card class="panel-card section-card" shadow="never">
    <template #header>
      <div class="panel-head">
        <div>
          <p class="panel-kicker">{{ eyebrow }}</p>
          <h3>{{ title }}</h3>
        </div>
        <slot name="action" />
      </div>
    </template>
    <slot />
  </el-card>
</template>

<script setup lang="ts">
defineProps<{
  title: string;
  eyebrow: string;
}>();
</script>
