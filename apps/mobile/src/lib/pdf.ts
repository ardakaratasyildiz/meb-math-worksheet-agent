import type { Worksheet } from "@soruatolyesi/shared";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";

import { fetchWorksheetPdfBase64 } from "./api";

/**
 * Worksheet'i backend'de PDF'e çevirir, cihaza (cache) yazar ve native paylaşım
 * sayfasını açar (WhatsApp, e-posta, kaydet…). Katil senaryo: "üret → PDF → paylaş".
 */
export async function shareWorksheetPdf(
  worksheet: Worksheet,
  opts: { includeAnswerKey?: boolean; includeSolutions?: boolean } = {},
): Promise<void> {
  const base64 = await fetchWorksheetPdfBase64(worksheet, opts);

  const dir = FileSystem.cacheDirectory;
  if (!dir) throw new Error("Geçici dizin bulunamadı.");
  const fileUri = `${dir}calisma-kagidi.pdf`;

  await FileSystem.writeAsStringAsync(fileUri, base64, {
    encoding: FileSystem.EncodingType.Base64,
  });

  if (!(await Sharing.isAvailableAsync())) {
    throw new Error("Paylaşım bu cihazda kullanılamıyor.");
  }
  await Sharing.shareAsync(fileUri, {
    mimeType: "application/pdf",
    UTI: "com.adobe.pdf",
    dialogTitle: "Çalışma kağıdını paylaş",
  });
}
