export interface StoreProduct {
  image_url: string;
  price: string | null;
  cart_adds: string | null;
  sales: string | null;
  title?: string | null;
  title_pt?: string | null;
  source_url?: string | null;
  category_label?: string | null;
  category_label_pt?: string | null;
  category_id?: string | null;
}

export interface RankedStore {
  rank: number;
  ranking_type?: string | null;
  category_label?: string | null;
  category_label_pt?: string | null;
  category_id?: string | null;
  region?: string | null;
  supplier_id?: string | null;
  member_id?: string | null;
  source_method?: string | null;
  consecutive_years: number | null;
  supplier_name: string;
  supplier_name_pt?: string | null;
  years_in_operation: number | null;
  repurchase_rate: number | null;
  response_rate: number | null;
  monthly_sales: string | null;
  top_products: StoreProduct[];
  review_snippet: string | null;
  source_url: string;
  source_label?: string | null;
  page_title: string | null;
  scraped_at: string;
}

export interface ListingProduct {
  row_id: string | number; // primary key part of (run_id, run_kind, row_id), used for updates
  offer_id: string | null;
  title: string | null;
  product_id?: string | null;
  price_min: number | null;
  price_raw: string | null;
  moq_raw: string | null;
  image_url: string | null;
  supplier_name: string | null;
  supplier_name_pt?: string | null;
  title_pt?: string | null;
  supplier_url: string | null;
  region?: string | null;
  category_label?: string | null;
  category_label_pt?: string | null;
  supplier_id?: string | null;
  category_name?: string | null;
  product_url?: string | null;
  sales_volume: string | null;
  repurchase_rate: number | null;
  rating?: number | null;
  category?: string | null;
  main_specification?: string | null;
  models?: string[] | null;
  specifications?: string[] | null;
  model_options?: string[] | null;
  variant_prices?: string[] | null;
  moq?: string | null;
  source_url?: string | null;
  ranking_badge: string | null;
  all_images?: string[] | null;
  video_url?: string | null;
  city?: string | null;
  certifications?: string[] | null;
  ranking_badges?: string[] | null;
  category_ids: string | null;
  keyword: string | null;
  page: number;
  sort: string;
  scraped_at: string;
}

export interface RunSummary {
  started_at?: string;
  finished_at?: string;
  total_products?: number;
  total_stores?: number;
  output_dir?: string;
  [key: string]: unknown;
}

export interface RunInfo {
  id: string;
  path: string;
  updated_at: string;
  count: number;
  summary: RunSummary | null;
}

export interface SupplierProfile {
  id: string;
  name: string;
  region: string | null;
  category_labels: string[];
  category_ids: string[];
  ranking: RankedStore | null;
  products: ListingProduct[];
  source_urls: string[];
  supplier_url?: string | null;
}