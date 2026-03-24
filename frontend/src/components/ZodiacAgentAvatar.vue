<template>
  <div class="zodiac-avatar" :class="[`zodiac-avatar--${normalizedKey}`, { 'zodiac-avatar--compact': compact }]">
    <svg viewBox="0 0 120 120" class="zodiac-avatar__svg" aria-hidden="true">
      <defs>
        <linearGradient :id="gradientId" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%" :stop-color="visual.secondary" />
          <stop offset="100%" :stop-color="visual.primary" />
        </linearGradient>
      </defs>

      <rect x="8" y="8" width="104" height="104" rx="30" :fill="`url(#${gradientId})`" />

      <g v-if="['rat', 'monkey', 'dog'].includes(normalizedKey)">
        <circle cx="34" cy="36" r="13" :fill="visual.secondary" opacity="0.95" />
        <circle cx="86" cy="36" r="13" :fill="visual.secondary" opacity="0.95" />
      </g>

      <g v-if="normalizedKey === 'rabbit'">
        <rect x="26" y="14" width="18" height="34" rx="10" :fill="visual.secondary" />
        <rect x="76" y="14" width="18" height="34" rx="10" :fill="visual.secondary" />
      </g>

      <g v-if="normalizedKey === 'ox' || normalizedKey === 'goat'">
        <path d="M26 34 C18 18, 40 14, 42 32" fill="none" :stroke="visual.secondary" stroke-width="8" stroke-linecap="round" />
        <path d="M94 34 C102 18, 80 14, 78 32" fill="none" :stroke="visual.secondary" stroke-width="8" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'dragon'">
        <path d="M28 36 C24 22, 40 18, 46 28" fill="none" :stroke="visual.secondary" stroke-width="8" stroke-linecap="round" />
        <path d="M92 36 C96 22, 80 18, 74 28" fill="none" :stroke="visual.secondary" stroke-width="8" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'horse'">
        <path d="M30 28 L44 18 L46 34" :fill="visual.secondary" />
        <path d="M90 28 L76 18 L74 34" :fill="visual.secondary" />
      </g>

      <g v-if="normalizedKey === 'rooster'">
        <circle cx="46" cy="24" r="8" fill="#FDBA74" />
        <circle cx="60" cy="18" r="9" fill="#F87171" />
        <circle cx="74" cy="24" r="8" fill="#FB7185" />
      </g>

      <g v-if="normalizedKey === 'tiger'">
        <path d="M28 30 L42 20 L44 36" :fill="visual.secondary" />
        <path d="M92 30 L78 20 L76 36" :fill="visual.secondary" />
      </g>

      <g v-if="normalizedKey === 'snake'">
        <path d="M26 34 C34 18, 50 18, 54 34" fill="none" :stroke="visual.secondary" stroke-width="8" stroke-linecap="round" />
        <path d="M94 34 C86 18, 70 18, 66 34" fill="none" :stroke="visual.secondary" stroke-width="8" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'pig'">
        <path d="M28 30 L42 22 L42 38" :fill="visual.secondary" />
        <path d="M92 30 L78 22 L78 38" :fill="visual.secondary" />
      </g>

      <circle cx="60" cy="62" r="34" fill="#FFF8F2" />

      <g v-if="normalizedKey === 'tiger'">
        <path d="M42 42 L46 52" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
        <path d="M60 38 L60 50" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
        <path d="M78 42 L74 52" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'dragon'">
        <path d="M34 62 C30 48, 40 42, 46 46" fill="none" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
        <path d="M86 62 C90 48, 80 42, 74 46" fill="none" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'rat'">
        <path d="M28 66 H40" :stroke="visual.accent" stroke-width="3" stroke-linecap="round" />
        <path d="M80 66 H92" :stroke="visual.accent" stroke-width="3" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'snake'">
        <path d="M46 70 Q60 82 74 70" fill="none" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
      </g>

      <circle cx="48" cy="60" r="4.5" fill="#1F2937" />
      <circle cx="72" cy="60" r="4.5" fill="#1F2937" />

      <g v-if="normalizedKey === 'pig'">
        <ellipse cx="60" cy="74" rx="15" ry="11" :fill="visual.secondary" />
        <circle cx="55" cy="74" r="2.8" fill="#1F2937" opacity="0.5" />
        <circle cx="65" cy="74" r="2.8" fill="#1F2937" opacity="0.5" />
      </g>
      <g v-else-if="normalizedKey === 'rooster'">
        <path d="M60 70 L52 78 H68 Z" fill="#F59E0B" />
      </g>
      <g v-else-if="normalizedKey === 'dog'">
        <path d="M52 74 Q60 82 68 74" fill="none" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
      </g>
      <g v-else>
        <path d="M50 74 Q60 82 70 74" fill="none" :stroke="visual.accent" stroke-width="4" stroke-linecap="round" />
      </g>

      <g v-if="normalizedKey === 'monkey'">
        <circle cx="40" cy="68" r="10" fill="#F7D7B0" />
        <circle cx="80" cy="68" r="10" fill="#F7D7B0" />
      </g>
      <g v-if="normalizedKey === 'horse'">
        <path d="M58 28 Q44 42 46 60" fill="none" :stroke="visual.accent" stroke-width="5" stroke-linecap="round" />
      </g>
    </svg>

    <div v-if="showLabel" class="zodiac-avatar__meta">
      <strong>{{ visual.label }}</strong>
      <span>{{ visual.description }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

import { zodiacAgentMap } from "../data/zodiacAgents";

const props = withDefaults(
  defineProps<{
    animalKey?: string | null;
    showLabel?: boolean;
    compact?: boolean;
  }>(),
  {
    animalKey: "dragon",
    showLabel: false,
    compact: false,
  }
);

const normalizedKey = computed(() => props.animalKey || "dragon");
const visual = computed(() => zodiacAgentMap[normalizedKey.value] ?? zodiacAgentMap.dragon);
const gradientId = computed(() => `zodiac-avatar-${visual.value.key}`);
</script>
