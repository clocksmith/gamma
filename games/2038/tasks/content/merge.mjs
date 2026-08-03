function identityFor(entry) {
  if (!entry || typeof entry !== "object" || Array.isArray(entry)) return undefined;
  for (const key of ["id", "factionId"]) {
    if (typeof entry[key] === "string") return { key, value: entry[key] };
  }
  return undefined;
}

export function mergeContent(base, overlay, label, trail = []) {
  if (Array.isArray(overlay)) {
    if (!Array.isArray(base)) {
      throw new Error(`Content overlay type mismatch in ${label} at ${trail.join(".")}`);
    }
    const identities = overlay.map(identityFor);
    if (identities.every(Boolean)) {
      const merged = [...base];
      for (let index = 0; index < overlay.length; index += 1) {
        const identity = identities[index];
        const baseIndex = base.findIndex(
          (entry) => entry?.[identity.key] === identity.value
        );
        if (baseIndex < 0) {
          throw new Error(
            `Unknown overlay identity in ${label}: ${identity.key}=${identity.value}`
          );
        }
        merged[baseIndex] = mergeContent(
          base[baseIndex],
          overlay[index],
          label,
          [...trail, `${identity.key}=${identity.value}`]
        );
      }
      return merged;
    }
    if (
      overlay.length === base.length &&
      overlay.every((entry) => entry && typeof entry === "object" && !Array.isArray(entry)) &&
      base.every((entry) => entry && typeof entry === "object" && !Array.isArray(entry))
    ) {
      return base.map((entry, index) =>
        mergeContent(entry, overlay[index], label, [...trail, String(index)])
      );
    }
    return overlay;
  }
  if (overlay && typeof overlay === "object") {
    if (!base || typeof base !== "object" || Array.isArray(base)) {
      throw new Error(`Content overlay type mismatch in ${label} at ${trail.join(".")}`);
    }
    const merged = { ...base };
    for (const [key, value] of Object.entries(overlay)) {
      merged[key] = Object.prototype.hasOwnProperty.call(base, key)
        ? mergeContent(base[key], value, label, [...trail, key])
        : value;
    }
    return merged;
  }
  return overlay;
}
