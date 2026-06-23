'use server';

import { query } from '@/lib/db-pg';

export async function updateListingTitle(rowId: number, title: string): Promise<{ success: boolean; error?: string }> {
  if (!rowId || !title?.trim()) {
    return { success: false, error: 'Invalid rowId or title' };
  }

  try {
    await query(
      'UPDATE listing_products SET title = $1 WHERE row_id = $2',
      [title.trim(), rowId]
    );
    return { success: true };
  } catch (error) {
    console.error('Failed to update title for row_id', rowId, error);
    return { success: false, error: 'Database error' };
  }
}
