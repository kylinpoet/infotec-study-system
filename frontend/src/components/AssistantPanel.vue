<template>
  <aside class="surface-card assistant-panel">
    <p class="card-label">{{ eyebrow }}</p>
    <h3>{{ title }}</h3>
    <p class="card-note">{{ subtitle }}</p>
    <button
      v-for="suggestion in suggestions"
      :key="suggestion"
      class="assistant-chip"
      type="button"
      @click="$emit('select', suggestion)"
    >
      {{ suggestion }}
    </button>
  </aside>
</template>

<script setup lang="ts">
defineProps<{
  eyebrow: string;
  title: string;
  subtitle: string;
  suggestions: string[];
}>();

defineEmits<{
  select: [value: string];
}>();
</script>

