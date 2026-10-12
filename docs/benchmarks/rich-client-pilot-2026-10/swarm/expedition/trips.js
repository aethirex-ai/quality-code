export const TRIPS = {
  ridge: {
    id: 'ridge', name: 'RIDGE', terrain: 'alpine', place: 'The high routes of the Engadine', region: 'Swiss Alps', days: 7, priceCents: 240000, image: 'assets/alpine.png',
    intro: 'A measured crossing between high pasture, stone villages and the quiet blue of the upper valleys.',
    route: ['Samedan', 'Val Roseg', 'Fuorcla Surlej', 'Silvaplana', 'Fex Valley', 'Sils', 'St. Moritz'],
    inclusions: ['Six nights in small mountain inns', 'Daily luggage transfer', 'Rail transfers within the route', 'Route notes and local host'],
    itinerary: [
      ['01', 'Arrive in the upper valley', 'Meet in Samedan, settle into a family-run inn and walk the old lanes before a shared welcome supper.'],
      ['02', 'Along the river to Roseg', 'Follow the Inn through larch forest to Val Roseg. A horse-drawn carriage option covers the final valley stretch; overnight at a quiet mountain guesthouse.'],
      ['03', 'The glacier viewpoint', 'Climb steadily to a balcony above the Roseg glacier, pause for a long picnic, then return by the same marked valley path.'],
      ['04', 'Cross to Surlej', 'Take the lift from Corvatsch to the high traverse, then walk to Fuorcla Surlej and descend to a lakeside inn.'],
      ['05', 'A slow day at the water', 'Choose a lakeshore walk or a short boat crossing on Silvaplana. The afternoon is free for the village and its small cafés.'],
      ['06', 'The Fex Valley', 'Walk a gentle route through the Fex Valley’s stone hamlets, with time to visit a local mill before returning to Sils.'],
      ['07', 'Last light in Sils', 'A final morning path above the lake, then an unhurried departure from the Engadine rail line.']
    ]
  },
  fjord: {
    id: 'fjord', name: 'FJORD', terrain: 'coastal', place: 'A coast of islands and inlets', region: 'Norwegian west coast', days: 5, priceCents: 180000, image: 'assets/fjord.png',
    intro: 'A salt-air passage by local ferry and footpath, with time to watch the weather change over the water.',
    route: ['Bergen', 'Lofthus', 'Ulvik', 'Rosendal', 'Bergen'],
    inclusions: ['Four nights in coastal guesthouses', 'Local ferry passages', 'Breakfast each morning', 'Printed field journal'],
    itinerary: [
      ['01', 'Harbour, then hillside', 'Gather in Bergen’s old harbour quarter and travel by ferry to a small fjord-side guesthouse in Lofthus.'],
      ['02', 'Orchard paths', 'Walk between fruit farms and the water on an old hillside lane. A local kitchen prepares a seasonal lunch before the ferry to Ulvik.'],
      ['03', 'The quiet inlet', 'Follow the shoreline to a sheltered inlet, with a short guided boat passage and an evening at a family-run inn.'],
      ['04', 'Rosendal and the garden', 'Cross the fjord to Rosendal, visit the historic barony gardens and take a low coastal path to the village.'],
      ['05', 'Back to the harbour', 'Return to Bergen by coastal ferry, leaving time for a final walk along the wharf.']
    ]
  },
  desert: {
    id: 'desert', name: 'DESERT', terrain: 'desert', place: 'The red stone country', region: 'Wadi Rum, Jordan', days: 6, priceCents: 210000, image: null,
    intro: 'A small-scale passage through sandstone valleys, by foot and with local drivers, paced for shade and stillness.',
    route: ['Aqaba', 'Disah', 'Jabal Umm ad Dami', 'Khazali Canyon', 'Wadi Rum', 'Aqaba'],
    inclusions: ['Five nights in locally hosted camps and inns', 'Ground transfers from Aqaba', 'Shared meals on route', 'Route notes and local host'],
    itinerary: [
      ['01', 'Arrive at the edge', 'Meet in Aqaba and transfer north to a locally hosted camp at Disah. Share a simple supper and orientation.'],
      ['02', 'Sandstone corridors', 'Travel by local 4×4 between narrow valleys, stepping out for short walks and a shaded tea stop with a Bedouin host.'],
      ['03', 'A high desert morning', 'Set out before the heat for a guided walk on a lower ridge near Jabal Umm ad Dami, then return to camp for a quiet afternoon.'],
      ['04', 'The canyon and its marks', 'Walk through Khazali Canyon with a local guide, pausing to read the landscape and its historic inscriptions.'],
      ['05', 'Open country', 'Cross a broad basin by local vehicle with several short walks, then spend the last night beneath a wide desert sky.'],
      ['06', 'Return to Aqaba', 'A morning transfer brings the group back to Aqaba for onward travel.']
    ]
  }
};

export const STORAGE_KEY = 'meridian.trip.v1';
export const GUIDE_CENTS = 60000;
export const hasTrip = id => typeof id === 'string' && Object.hasOwn(TRIPS, id);
export const validTravelers = (value, previous = 1) => {
  const n = Number(value);
  return Number.isInteger(n) && n >= 1 && n <= 6 ? n : previous;
};
export function readTrip(raw) {
  try {
    const value = JSON.parse(raw);
    const id = hasTrip(value?.id) ? value.id : 'ridge';
    return { id, travelers: validTravelers(value?.travelers, 1), guide: value?.guide === true };
  } catch { return { id: 'ridge', travelers: 1, guide: false }; }
}
export const totalCents = ({ id, travelers, guide }) => TRIPS[hasTrip(id) ? id : 'ridge'].priceCents * validTravelers(travelers) + (guide ? GUIDE_CENTS : 0);
export const money = cents => new Intl.NumberFormat('en-GB', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(cents / 100);
