# Panduan Penggunaan WIB Timezone

## Filter Jinja2 yang Tersedia

### 1. `to_wib` - Datetime lengkap
Format: `DD-MM-YYYY HH:MM WIB`
```html
{{ lead.created_at|to_wib }}
<!-- Output: 17-02-2026 11:30 WIB -->
```

### 2. `to_wib_date` - Tanggal saja
Format: `DD-MM-YYYY`
```html
{{ lead.created_at|to_wib_date }}
<!-- Output: 17-02-2026 -->
```

### 3. `to_wib_time` - Waktu saja  
Format: `HH:MM WIB`
```html
{{ lead.created_at|to_wib_time }}
<!-- Output: 11:30 WIB -->
```

## Cara Pakai di Template

### Contoh di Dashboard
```html
<p>Lead dibuat: {{ lead.created_at|to_wib }}</p>
<p>Terakhir update: {{ lead.updated_at|to_wib }}</p>
<p>Sent at: {{ lead.sent_to_mailketing_at|to_wib }}</p>
```

### Contoh di Tabel
```html
<td>{{ lead.created_at|to_wib }}</td>
<td>{{ lead.follow_up_start|to_wib_date }}</td>
```

### Handling None/NULL
Filter otomatis return `-` jika datetime None/NULL:
```html
{{ lead.closed_at|to_wib }}
<!-- Output: "-" jika NULL -->
```

## Perubahan yang Sudah Diterapkan

1. ✅ Timezone configuration: `WIB = pytz.timezone('Asia/Jakarta')`
2. ✅ Helper function: `get_wib_now()` untuk get waktu sekarang dalam WIB
3. ✅ 3 Jinja2 filters: `to_wib`, `to_wib_date`, `to_wib_time`
4. ✅ Auto-convert UTC → WIB di semua template yang pakai filter

## Update Template yang Sudah Ada

Ganti:
```html
{{ lead.created_at }}  <!-- Format UTC raw -->
```

Jadi:
```html
{{ lead.created_at|to_wib }}  <!-- Format WIB readable -->
```
