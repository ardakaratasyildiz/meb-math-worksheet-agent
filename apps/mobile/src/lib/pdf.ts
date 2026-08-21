import type { Worksheet } from "@soruatolyesi/shared";
import * as FileSystem from "expo-file-system/legacy";
import * as Print from "expo-print";
import * as Sharing from "expo-sharing";

import { fetchWorksheetPdfBase64 } from "./api";

type PdfOpts = {
  includeAnswerKey?: boolean;
  includeSolutions?: boolean;
  /** White-label ust bilgi (kurum/ogretmen markasi) — bkz. lib/branding.ts. */
  brandName?: string;
  brandSubtitle?: string;
  brandLogo?: string;
};

/** Worksheet'i backend'de PDF'e çevirir, cihaza (cache) yazar → dosya URI'si döner. */
async function buildWorksheetPdfFile(worksheet: Worksheet, opts: PdfOpts): Promise<string> {
  const base64 = await fetchWorksheetPdfBase64(worksheet, opts);
  const dir = FileSystem.cacheDirectory;
  if (!dir) throw new Error("Geçici dizin bulunamadı.");
  const fileUri = `${dir}calisma-kagidi.pdf`;
  await FileSystem.writeAsStringAsync(fileUri, base64, {
    encoding: FileSystem.EncodingType.Base64,
  });
  return fileUri;
}

/**
 * PDF'i üretir ve NATIVE ÖNİZLEME açar (Print dialog: sayfa sayfa gez → oradan
 * yazdır / kaydet / paylaş). iOS + Android ortak. Paylaşmadan önce içeriği görmek için.
 */
export async function previewWorksheetPdf(worksheet: Worksheet, opts: PdfOpts = {}): Promise<void> {
  const fileUri = await buildWorksheetPdfFile(worksheet, opts);
  await Print.printAsync({ uri: fileUri });
}

/**
 * Worksheet'i PDF'e çevirir ve native paylaşım sayfasını açar (WhatsApp, e-posta,
 * kaydet…). Katil senaryo: "üret → PDF → paylaş".
 */
export async function shareWorksheetPdf(worksheet: Worksheet, opts: PdfOpts = {}): Promise<void> {
  const fileUri = await buildWorksheetPdfFile(worksheet, opts);
  if (!(await Sharing.isAvailableAsync())) {
    throw new Error("Paylaşım bu cihazda kullanılamıyor.");
  }
  await Sharing.shareAsync(fileUri, {
    mimeType: "application/pdf",
    UTI: "com.adobe.pdf",
    dialogTitle: "Çalışma kağıdını paylaş",
  });
}
