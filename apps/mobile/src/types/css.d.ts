// CSS import'ları için tip bildirimi (Metro/NativeWind bunları çalışma zamanında
// çözer; TypeScript'in bilmesi için deklarasyon). Expo default template global.css
// + *.module.css (web) kullanır.
declare module "*.css";
declare module "*.module.css" {
  const classes: { readonly [key: string]: string };
  export default classes;
}
