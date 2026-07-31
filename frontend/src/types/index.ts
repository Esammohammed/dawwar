export type Role = 'buyer' | 'seller' | 'staff' | 'admin';

export interface User {
  id: string;
  phone: string;
  email?: string;
  full_name: string;
  role: Role;
  is_phone_verified: boolean;
  telegram_id?: string;
  created_at: string;
}

export interface Developer {
  id: string;
  name: string;
  commercial_register_no?: string;
  contact_phone: string;
  contact_email?: string;
  logo?: string;
  verified: boolean;
  commission_terms?: Record<string, any>;
  notes?: string;
  created_at: string;
}

export type ProjectType = 'government' | 'developer';
export type ProjectStatus = 'announced' | 'open_for_booking' | 'under_construction' | 'delivered';

export interface Project {
  id: string;
  type: ProjectType;
  developer?: string;
  developer_details?: Developer;
  name: string;
  slug: string;
  governorate: string;
  city: string;
  district?: string;
  description?: string;
  status: ProjectStatus;
  details?: Record<string, any>;
  cover_image?: string;
  created_at: string;
}

export type ListingType = 'resale' | 'developer_unit';
export type FinishingType = 'core_shell' | 'semi' | 'fully' | 'lux';
export type ListingStatus = 'draft' | 'under_review' | 'active' | 'reserved' | 'sold' | 'archived';
export type MediaKind = 'photo' | 'video' | 'floorplan';

export interface Media {
  id: string;
  file: string;
  kind: MediaKind;
  sort_order: number;
}

export interface InstallmentPlan {
  down_payment?: number;
  remaining_amount?: number;
  quarterly_installment?: number;
  years_remaining?: number;
  years?: number;
}

export interface Listing {
  id: string;
  type: ListingType;
  project?: string;
  project_details?: Project;
  seller?: string;
  seller_name?: string;
  seller_phone?: string;
  developer?: string;
  developer_details?: Developer;
  title: string;
  description?: string;
  area_sqm: number;
  bedrooms: number;
  bathrooms: number;
  floor?: number;
  finishing?: FinishingType;
  unit_attributes?: Record<string, any>;
  governorate: string;
  city: string;
  district?: string;
  asking_price: number;
  currency: string;
  negotiable: boolean;
  original_price?: number;
  amount_paid?: number;
  transfer_fee?: number;
  installment_plan?: InstallmentPlan;
  status: ListingStatus;
  published_at?: string;
  created_at: string;
  media: Media[];
}

export interface Announcement {
  id: string;
  source: string;
  source_name: string;
  project?: string;
  title: string;
  body: string;
  ai_summary?: string;
  source_url: string;
  status: string;
  published_at?: string;
  scraped_at: string;
}

export interface Application {
  id: string;
  user: string;
  project: string;
  project_details?: Project;
  status: 'collecting_docs' | 'ready' | 'submitted' | 'accepted' | 'rejected' | 'refunded';
  documents: Array<{ name: string; s3_key: string; uploaded_at: string }>;
  service_fee: number;
  paid: boolean;
  submitted_at?: string;
  notes?: string;
  created_at: string;
}

export interface Booking {
  id: string;
  listing: string;
  listing_details?: Listing;
  user: string;
  deposit_amount: number;
  status: 'pending_payment' | 'confirmed' | 'expired' | 'cancelled';
  expires_at: string;
  created_at: string;
}
