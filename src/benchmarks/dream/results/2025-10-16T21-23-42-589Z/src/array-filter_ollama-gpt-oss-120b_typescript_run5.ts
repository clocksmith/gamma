export function customFilter<T>(array: T[], predicate: (item: T) => boolean): T[] {
    return array.filter(predicate);
}
