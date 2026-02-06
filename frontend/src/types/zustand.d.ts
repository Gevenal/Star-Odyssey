// Type declaration for zustand to help TypeScript resolve the module
declare module 'zustand' {
  export function create<T>(fn: (set: any, get: any) => T): () => T;
}
