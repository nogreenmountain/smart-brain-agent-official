import { redirect } from 'next/navigation';

export default function MonitorSetupPage() {
  redirect('/workday?view=records');
}
