export function customFilter<T>(array: T[], predicate: (item: T) => boolean): T[] {
    const result: T[] = [];
    for (const element of array) {
        if (predicate(element)) {
            result.push(element);
        }
    }
    return result;
}
